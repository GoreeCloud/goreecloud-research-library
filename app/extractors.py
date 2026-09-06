from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from io import BytesIO
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass
class ExtractedDocument:
    title: str
    author: str
    publisher: str
    published_at: str
    canonical_url: str
    source_type: str
    content: str
    excerpt: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _clean_lines(text: str) -> str:
    lines = []
    previous_blank = False
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            if not previous_blank and lines:
                lines.append("")
            previous_blank = True
            continue
        previous_blank = False
        lines.append(line)
    return "\n".join(lines).strip()


def _meta(soup: BeautifulSoup, *keys: str) -> str:
    for key in keys:
        tag = soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"property": key})
        if tag and tag.get("content"):
            return str(tag.get("content")).strip()
    return ""


def _safe_canonical(base_url: str, candidate: str) -> str:
    if not candidate:
        return base_url
    absolute = urljoin(base_url, candidate)
    parsed = urlsplit(absolute)
    return absolute if parsed.scheme in {"http", "https"} and parsed.hostname else base_url


def extract_html(data: bytes, url: str, max_chars: int) -> ExtractedDocument:
    soup = BeautifulSoup(data, "html.parser")
    for element in soup(["script", "style", "noscript", "template", "svg", "canvas", "form"]):
        element.decompose()

    title = _meta(soup, "og:title", "twitter:title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        heading = soup.find("h1")
        title = heading.get_text(" ", strip=True) if heading else url

    author = _meta(soup, "author", "article:author", "byl")
    publisher = _meta(soup, "og:site_name", "publisher", "application-name")
    published_at = _meta(
        soup,
        "article:published_time",
        "datePublished",
        "date",
        "dc.date",
        "dcterms.date",
    )

    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical_url = _safe_canonical(url, str(canonical_tag.get("href", "")) if canonical_tag else "")

    candidates = [soup.find("article"), soup.find("main")]
    body = None
    for candidate in candidates:
        if candidate and len(candidate.get_text(" ", strip=True)) >= 200:
            body = candidate
            break
    if body is None:
        body = soup.body or soup
        for element in body.find_all(["nav", "footer", "header", "aside"]):
            element.decompose()

    content = _clean_lines(body.get_text("\n", strip=True))[:max_chars]
    excerpt = re.sub(r"\s+", " ", content).strip()[:500]
    return ExtractedDocument(
        title=title[:500],
        author=author[:300],
        publisher=publisher[:300],
        published_at=published_at[:100],
        canonical_url=canonical_url,
        source_type="web",
        content=content,
        excerpt=excerpt,
    )


def extract_pdf(data: bytes, url: str, max_chars: int) -> ExtractedDocument:
    reader = PdfReader(BytesIO(data))
    metadata = reader.metadata or {}
    chunks: list[str] = []
    total = 0
    for page in reader.pages[:200]:
        text = page.extract_text() or ""
        if not text:
            continue
        remaining = max_chars - total
        if remaining <= 0:
            break
        chunk = text[:remaining]
        chunks.append(chunk)
        total += len(chunk)
    content = _clean_lines("\n\n".join(chunks))
    title = str(metadata.get("/Title") or "").strip() or url.rsplit("/", 1)[-1] or "PDF source"
    author = str(metadata.get("/Author") or "").strip()
    excerpt = re.sub(r"\s+", " ", content).strip()[:500]
    return ExtractedDocument(
        title=title[:500],
        author=author[:300],
        publisher="",
        published_at="",
        canonical_url=url,
        source_type="pdf",
        content=content,
        excerpt=excerpt,
    )


def extract_text(data: bytes, url: str, max_chars: int) -> ExtractedDocument:
    content = data.decode("utf-8", errors="replace")[:max_chars]
    content = _clean_lines(content)
    title = url.rsplit("/", 1)[-1] or url
    return ExtractedDocument(
        title=title[:500],
        author="",
        publisher="",
        published_at="",
        canonical_url=url,
        source_type="text",
        content=content,
        excerpt=re.sub(r"\s+", " ", content).strip()[:500],
    )


def content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()
