from __future__ import annotations

import re
from urllib.parse import urlsplit


def _date_only(value: str) -> str:
    return value[:10] if value else ""


def _date_parts(value: str) -> list[list[int]]:
    value = _date_only(value)
    if not value:
        return []
    try:
        return [[int(part) for part in value.split("-") if part]]
    except ValueError:
        return []


def markdown_citation(source: dict) -> str:
    author = source.get("author") or source.get("publisher") or "Unknown author"
    title = source.get("title") or source.get("url") or "Untitled source"
    publisher = source.get("publisher") or urlsplit(source.get("url", "")).hostname or ""
    published = _date_only(source.get("published_at", ""))
    accessed = _date_only(source.get("accessed_at", ""))
    pieces = [f'{author}. “{title}.”']
    if publisher and publisher != author:
        pieces.append(publisher + ".")
    if published:
        pieces.append(published + ".")
    pieces.append(source.get("url", "") + ".")
    if accessed:
        pieces.append(f"Accessed {accessed}.")
    return " ".join(piece for piece in pieces if piece)


def bibtex_citation(source: dict) -> str:
    title = source.get("title") or "Untitled source"
    author = source.get("author") or source.get("publisher") or "Unknown"
    year_match = re.search(r"(19|20)\d{2}", source.get("published_at", ""))
    year = year_match.group(0) if year_match else ""
    slug = re.sub(r"[^a-z0-9]+", "", (author.split()[-1] + title.split()[0]).lower())[:24] or "source"
    key = f"{slug}{year or 'nd'}"
    values = {
        "title": title,
        "author": author,
        "year": year,
        "url": source.get("url", ""),
        "urldate": _date_only(source.get("accessed_at", "")),
    }
    lines = [f"@online{{{key},"]
    for field, value in values.items():
        if value:
            clean = str(value).replace("{", "\\{").replace("}", "\\}")
            lines.append(f"  {field} = {{{clean}}},")
    lines.append("}")
    return "\n".join(lines)


def csl_json_citation(source: dict) -> dict:
    author = source.get("author", "").strip()
    item: dict = {
        "id": f"goreecloud-source-{source.get('id', 'unknown')}",
        "type": "webpage",
        "title": source.get("title") or source.get("url") or "Untitled source",
        "URL": source.get("url", ""),
    }
    if author:
        item["author"] = [{"literal": author}]
    if source.get("publisher"):
        item["publisher"] = source["publisher"]
    issued = _date_parts(source.get("published_at", ""))
    if issued:
        item["issued"] = {"date-parts": issued}
    accessed = _date_parts(source.get("accessed_at", ""))
    if accessed:
        item["accessed"] = {"date-parts": accessed}
    return item


def ris_citation(source: dict) -> str:
    lines = ["TY  - ELEC"]
    if source.get("title"):
        lines.append(f"TI  - {source['title']}")
    if source.get("author"):
        lines.append(f"AU  - {source['author']}")
    if source.get("publisher"):
        lines.append(f"PB  - {source['publisher']}")
    if source.get("published_at"):
        lines.append(f"PY  - {_date_only(source['published_at'])}")
    if source.get("url"):
        lines.append(f"UR  - {source['url']}")
    if source.get("accessed_at"):
        lines.append(f"Y2  - {_date_only(source['accessed_at'])}")
    lines.append("ER  -")
    return "\n".join(lines)
