from __future__ import annotations

from contextlib import asynccontextmanager
import csv
from io import StringIO
import json
import sqlite3

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from .citations import bibtex_citation, csl_json_citation, markdown_citation, ris_citation
from .config import settings
from .db import Database
from .fetcher import FetchError, fetch_and_extract


RESEARCH_CLASSIFICATIONS = [
    "verified-fact",
    "source-reported-vendor-claim",
    "direct-observation",
    "test-result",
    "inference",
    "recommendation",
    "decision",
    "planned-configuration",
    "assumption",
    "estimate",
    "historical",
    "unknown-verification-required",
]
SOURCE_CLASSIFICATIONS = [
    "goreecloud-authoritative",
    "external-primary",
    "independent-technical",
    "community-evidence",
    "retail-availability",
    "unknown-verification-required",
]
CONFIDENCE_LEVELS = ["high", "medium", "low", "unknown"]
RELATIONSHIP_TYPES = ["supports", "contradicts", "duplicates", "updates", "references", "contextualizes"]
RELATIONSHIP_STRENGTHS = ["high", "medium", "low", "unknown"]


db = Database(settings.database_path)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.initialize()
    yield


app = FastAPI(
    title="GoreeCloud Research Library",
    version="0.2.0-dev",
    description="Local-first source capture, evidence classification, research projects, and source relationships.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class CaptureRequest(BaseModel):
    url: HttpUrl


async def capture_url(url: str):
    result = await fetch_and_extract(url, settings)
    return db.save_capture(result.payload)


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    q: str = Query(default="", max_length=200),
    classification: str = Query(default="", max_length=100),
    error: str = Query(default="", max_length=500),
):
    sources = db.list_sources(q, classification)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "sources": sources,
            "q": q,
            "classification": classification,
            "source_classifications": SOURCE_CLASSIFICATIONS,
            "saved_searches": db.list_saved_searches(),
            "error": error,
        },
    )


@app.post("/capture")
async def capture(url: str = Form(...)):
    try:
        source, created, changed = await capture_url(url)
    except FetchError as exc:
        return RedirectResponse(url=f"/?error={str(exc)}", status_code=303)
    suffix = "created" if created else ("changed" if changed else "unchanged")
    return RedirectResponse(url=f"/sources/{source['id']}?capture={suffix}", status_code=303)


@app.post("/saved-searches")
def save_search(
    name: str = Form(..., min_length=1, max_length=120),
    query: str = Form("", max_length=200),
    classification: str = Form("", max_length=100),
):
    if classification and classification not in SOURCE_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid source classification")
    db.save_search(name, query, classification)
    return RedirectResponse(url="/", status_code=303)


@app.post("/saved-searches/{search_id}/delete")
def delete_saved_search(search_id: int):
    db.delete_saved_search(search_id)
    return RedirectResponse(url="/", status_code=303)


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={"projects": db.list_projects()},
    )


@app.post("/projects")
def create_project(
    name: str = Form(..., min_length=1, max_length=160),
    question: str = Form("", max_length=1000),
    description: str = Form("", max_length=5000),
    tags: str = Form("", max_length=1000),
):
    try:
        project = db.create_project(name, question, description, tags)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="A project with that name already exists") from exc
    return RedirectResponse(url=f"/projects/{project['id']}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: int):
    project = db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    sources = db.list_project_sources(project_id)
    relationships = db.list_project_relationships(project_id)
    relationship_summary = {value: 0 for value in RELATIONSHIP_TYPES}
    for relationship in relationships:
        kind = relationship["relationship"]
        if kind in relationship_summary:
            relationship_summary[kind] += 1
    return templates.TemplateResponse(
        request=request,
        name="project.html",
        context={
            "project": project,
            "sources": sources,
            "all_sources": db.all_sources(),
            "relationships": relationships,
            "relationship_types": RELATIONSHIP_TYPES,
            "relationship_strengths": RELATIONSHIP_STRENGTHS,
            "relationship_summary": relationship_summary,
        },
    )


@app.post("/projects/{project_id}/sources")
def add_project_source(
    project_id: int,
    source_id: int = Form(...),
    notes: str = Form("", max_length=2000),
):
    if db.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if db.get_source(source_id) is None:
        raise HTTPException(status_code=404, detail="Source not found")
    db.add_source_to_project(project_id, source_id, notes)
    return RedirectResponse(url=f"/projects/{project_id}#sources", status_code=303)


@app.post("/projects/{project_id}/sources/{source_id}/remove")
def remove_project_source(project_id: int, source_id: int):
    if db.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.remove_source_from_project(project_id, source_id)
    return RedirectResponse(url=f"/projects/{project_id}#sources", status_code=303)


@app.post("/projects/{project_id}/relationships")
def add_project_relationship(
    project_id: int,
    from_source_id: int = Form(...),
    to_source_id: int = Form(...),
    relationship: str = Form(...),
    strength: str = Form("medium"),
    note: str = Form("", max_length=5000),
):
    project_source_ids = {source["id"] for source in db.list_project_sources(project_id)}
    if from_source_id not in project_source_ids or to_source_id not in project_source_ids:
        raise HTTPException(status_code=400, detail="Both sources must belong to the project")
    if relationship not in RELATIONSHIP_TYPES:
        raise HTTPException(status_code=400, detail="Invalid relationship type")
    if strength not in RELATIONSHIP_STRENGTHS:
        raise HTTPException(status_code=400, detail="Invalid relationship strength")
    try:
        db.upsert_relationship(from_source_id, to_source_id, relationship, strength, note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url=f"/projects/{project_id}#relationships", status_code=303)


@app.get("/sources/{source_id}", response_class=HTMLResponse)
def source_detail(request: Request, source_id: int, capture: str = ""):
    source = db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return templates.TemplateResponse(
        request=request,
        name="source.html",
        context={
            "source": source,
            "snapshots": db.list_snapshots(source_id),
            "claims": db.list_claims(source_id),
            "research_classifications": RESEARCH_CLASSIFICATIONS,
            "source_classifications": SOURCE_CLASSIFICATIONS,
            "confidence_levels": CONFIDENCE_LEVELS,
            "capture": capture,
            "citation_markdown": markdown_citation(source),
            "citation_bibtex": bibtex_citation(source),
            "citation_csl": json.dumps(csl_json_citation(source), indent=2),
            "citation_ris": ris_citation(source),
            "projects": db.list_projects(),
            "source_projects": db.list_source_projects(source_id),
            "relationships": db.list_source_relationships(source_id),
        },
    )


@app.post("/sources/{source_id}/projects")
def add_source_project(
    source_id: int,
    project_id: int = Form(...),
    notes: str = Form("", max_length=2000),
):
    if db.get_source(source_id) is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if db.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.add_source_to_project(project_id, source_id, notes)
    return RedirectResponse(url=f"/sources/{source_id}#projects", status_code=303)


@app.post("/sources/{source_id}/refresh")
async def refresh_source(source_id: int):
    source = db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    try:
        updated, _, changed = await capture_url(source["url"])
    except FetchError as exc:
        return RedirectResponse(url=f"/sources/{source_id}?capture=error:{str(exc)}", status_code=303)
    return RedirectResponse(
        url=f"/sources/{updated['id']}?capture={'changed' if changed else 'unchanged'}", status_code=303
    )


@app.post("/sources/{source_id}/metadata")
def update_metadata(
    source_id: int,
    title: str = Form(""),
    author: str = Form(""),
    publisher: str = Form(""),
    published_at: str = Form(""),
    source_classification: str = Form("unknown-verification-required"),
    evidence_status: str = Form("source-reported-vendor-claim"),
    tags: str = Form(""),
    notes: str = Form(""),
):
    if source_classification not in SOURCE_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid source classification")
    if evidence_status not in RESEARCH_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid evidence status")
    source = db.update_source_metadata(
        source_id,
        {
            "title": title,
            "author": author,
            "publisher": publisher,
            "published_at": published_at,
            "source_classification": source_classification,
            "evidence_status": evidence_status,
            "tags": tags,
            "notes": notes,
        },
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return RedirectResponse(url=f"/sources/{source_id}", status_code=303)


@app.post("/sources/{source_id}/claims")
def add_claim(
    source_id: int,
    statement: str = Form(..., min_length=1, max_length=5000),
    classification: str = Form(...),
    confidence: str = Form("medium"),
    evidence_note: str = Form("", max_length=5000),
):
    if db.get_source(source_id) is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if classification not in RESEARCH_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid evidence classification")
    if confidence not in CONFIDENCE_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid confidence")
    db.add_claim(source_id, statement, classification, confidence, evidence_note)
    return RedirectResponse(url=f"/sources/{source_id}#claims", status_code=303)


@app.get("/sources/{source_id}/citation")
def citation(source_id: int, format: str = Query("markdown", pattern="^(markdown|bibtex|csl-json|ris)$")):
    source = db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if format == "bibtex":
        return PlainTextResponse(bibtex_citation(source))
    if format == "csl-json":
        return JSONResponse(csl_json_citation(source))
    if format == "ris":
        return PlainTextResponse(ris_citation(source))
    return PlainTextResponse(markdown_citation(source))


@app.get("/api/v1/sources")
def api_sources(q: str = "", classification: str = ""):
    return {"sources": db.list_sources(q, classification)}


@app.get("/api/v1/sources/{source_id}")
def api_source(source_id: int):
    source = db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    source["claims"] = db.list_claims(source_id)
    source["snapshots"] = db.list_snapshots(source_id)
    source["projects"] = db.list_source_projects(source_id)
    source["relationships"] = db.list_source_relationships(source_id)
    return source


@app.post("/api/v1/capture")
async def api_capture(body: CaptureRequest):
    try:
        source, created, changed = await capture_url(str(body.url))
    except FetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse({"source": source, "created": created, "changed": changed}, status_code=201 if created else 200)


@app.get("/api/v1/projects")
def api_projects():
    return {"projects": db.list_projects()}


@app.get("/api/v1/projects/{project_id}")
def api_project(project_id: int):
    project = db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project["sources"] = db.list_project_sources(project_id)
    project["relationships"] = db.list_project_relationships(project_id)
    return project


@app.get("/export.json")
def export_json():
    sources = db.all_sources()
    for source in sources:
        source["claims"] = db.list_claims(source["id"])
        source["snapshots"] = db.list_snapshots(source["id"])
        source["projects"] = db.list_source_projects(source["id"])
        source["relationships"] = db.list_source_relationships(source["id"])
    projects_export = []
    for project in db.list_projects(limit=500):
        project["sources"] = db.list_project_sources(project["id"])
        project["relationships"] = db.list_project_relationships(project["id"])
        projects_export.append(project)
    content = json.dumps(
        {
            "format": "goreecloud-research-library-export-v2",
            "sources": sources,
            "projects": projects_export,
            "saved_searches": db.list_saved_searches(),
        },
        indent=2,
    )
    headers = {"Content-Disposition": 'attachment; filename="goreecloud-research-library.json"'}
    return Response(content=content, media_type="application/json", headers=headers)


@app.get("/export.csv")
def export_csv():
    output = StringIO()
    fieldnames = [
        "id",
        "title",
        "url",
        "author",
        "publisher",
        "published_at",
        "source_type",
        "source_classification",
        "evidence_status",
        "tags",
        "accessed_at",
        "fetched_at",
        "content_hash",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for source in db.all_sources():
        writer.writerow({field: source.get(field, "") for field in fieldnames})
    headers = {"Content-Disposition": 'attachment; filename="goreecloud-research-library.csv"'}
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)


@app.get("/export.csl.json")
def export_csl_json():
    content = json.dumps([csl_json_citation(source) for source in db.all_sources()], indent=2)
    headers = {"Content-Disposition": 'attachment; filename="goreecloud-research-library.csl.json"'}
    return Response(content=content, media_type="application/json", headers=headers)


@app.get("/export.ris")
def export_ris():
    content = "\n\n".join(ris_citation(source) for source in db.all_sources())
    headers = {"Content-Disposition": 'attachment; filename="goreecloud-research-library.ris"'}
    return Response(content=content, media_type="application/x-research-info-systems", headers=headers)


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "goreecloud-research-library",
        "version": "0.2.0-dev",
        "schema_version": db.schema_version(),
        "fts": db.fts_enabled,
    }
