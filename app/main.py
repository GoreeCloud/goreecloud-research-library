from __future__ import annotations

from contextlib import asynccontextmanager
import csv
from io import StringIO
import json

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from .citations import bibtex_citation, markdown_citation
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


db = Database(settings.database_path)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.initialize()
    yield


app = FastAPI(
    title="GoreeCloud Research Library",
    version="0.1.0-dev",
    description="Local-first source capture, extraction, evidence classification, and research library.",
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
        },
    )


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


@app.get("/sources/{source_id}/citation", response_class=PlainTextResponse)
def citation(source_id: int, format: str = Query("markdown", pattern="^(markdown|bibtex)$")):
    source = db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return bibtex_citation(source) if format == "bibtex" else markdown_citation(source)


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
    return source


@app.post("/api/v1/capture")
async def api_capture(body: CaptureRequest):
    try:
        source, created, changed = await capture_url(str(body.url))
    except FetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse({"source": source, "created": created, "changed": changed}, status_code=201 if created else 200)


@app.get("/export.json")
def export_json():
    sources = db.all_sources()
    for source in sources:
        source["claims"] = db.list_claims(source["id"])
        source["snapshots"] = db.list_snapshots(source["id"])
    content = json.dumps({"format": "goreecloud-research-library-export-v1", "sources": sources}, indent=2)
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


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "service": "goreecloud-research-library",
        "version": "0.1.0-dev",
        "fts": db.fts_enabled,
    }
