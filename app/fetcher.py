from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from .config import Settings
from .extractors import content_hash, extract_html, extract_pdf, extract_text


SUPPORTED_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "text/markdown",
    "application/json",
    "application/xml",
    "text/xml",
    "application/rss+xml",
    "application/atom+xml",
    "application/pdf",
}


class FetchError(ValueError):
    pass


@dataclass
class FetchResult:
    payload: dict[str, object]


def normalize_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        raise FetchError("Enter a URL to capture.")
    if "://" not in raw_url:
        raw_url = "https://" + raw_url
    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise FetchError("Only http:// and https:// URLs are supported.")
    if not parsed.hostname:
        raise FetchError("The URL must contain a host name.")
    if parsed.username or parsed.password:
        raise FetchError("URLs containing embedded credentials are not allowed.")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    try:
        port = parsed.port
    except ValueError as exc:
        raise FetchError("The URL contains an invalid port.") from exc
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if port is not None:
        default = 443 if parsed.scheme == "https" else 80
        if port != default:
            netloc = f"{netloc}:{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme, netloc, path, parsed.query, ""))


async def _resolve_host(host: str, port: int) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    def resolve() -> list[str]:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        return list({record[4][0] for record in records})

    try:
        values = await asyncio.to_thread(resolve)
    except socket.gaierror as exc:
        raise FetchError(f"Could not resolve host: {host}") from exc
    if not values:
        raise FetchError(f"Could not resolve host: {host}")
    return [ipaddress.ip_address(value) for value in values]


async def validate_public_url(url: str, allow_private: bool = False) -> str:
    normalized = normalize_url(url)
    parsed = urlsplit(normalized)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = await _resolve_host(parsed.hostname or "", port)
    if not allow_private:
        blocked = [address for address in addresses if not address.is_global]
        if blocked:
            raise FetchError("The URL resolves to a private, local, reserved, or otherwise non-public address.")
    return normalized


async def _robots_allows(client: httpx.AsyncClient, url: str, settings: Settings) -> bool:
    if not settings.respect_robots_txt:
        return True
    parsed = urlsplit(url)
    robots_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
    try:
        response = await client.get(robots_url, follow_redirects=False)
    except httpx.HTTPError:
        return True
    if response.status_code in {401, 403}:
        return False
    if response.status_code != 200:
        return True
    if len(response.content) > 512 * 1024:
        return True
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(response.text.splitlines())
    return parser.can_fetch(settings.user_agent, url)


async def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    header = response.headers.get("content-length")
    if header:
        try:
            if int(header) > max_bytes:
                raise FetchError(f"Resource is larger than the {max_bytes} byte capture limit.")
        except ValueError:
            pass
    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise FetchError(f"Resource exceeded the {max_bytes} byte capture limit.")
        chunks.append(chunk)
    return b"".join(chunks)


async def fetch_and_extract(raw_url: str, settings: Settings) -> FetchResult:
    current = await validate_public_url(raw_url, settings.allow_private_fetch)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/pdf,application/json,application/xml,text/plain;q=0.9,*/*;q=0.1",
    }

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=False) as client:
        for hop in range(settings.max_redirects + 1):
            current = await validate_public_url(current, settings.allow_private_fetch)
            if not await _robots_allows(client, current, settings):
                raise FetchError("The site's robots.txt policy does not permit this research fetch.")
            try:
                async with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        if hop >= settings.max_redirects:
                            raise FetchError("The URL exceeded the redirect limit.")
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError("The server returned a redirect without a destination.")
                        current = urljoin(current, location)
                        continue
                    if response.status_code >= 400:
                        raise FetchError(f"The source returned HTTP {response.status_code}.")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    data = await _read_limited(response, settings.max_fetch_bytes)
                    status = response.status_code
            except httpx.TimeoutException as exc:
                raise FetchError("The source timed out while being fetched.") from exc
            except httpx.HTTPError as exc:
                raise FetchError(f"The source could not be fetched: {exc}") from exc
            break
        else:
            raise FetchError("The URL exceeded the redirect limit.")

    if not content_type:
        if data.startswith(b"%PDF"):
            content_type = "application/pdf"
        elif data.lstrip().startswith(b"<"):
            content_type = "text/html"
        else:
            content_type = "text/plain"
    if content_type not in SUPPORTED_TYPES:
        raise FetchError(f"Unsupported resource type: {content_type or 'unknown'}.")

    if content_type == "application/pdf":
        document = extract_pdf(data, current, settings.max_extract_chars)
    elif content_type in {"text/html", "application/xhtml+xml"}:
        document = extract_html(data, current, settings.max_extract_chars)
    else:
        document = extract_text(data, current, settings.max_extract_chars)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, object] = document.to_dict()
    payload.update(
        {
            "url": current,
            "content_hash": content_hash(document.content),
            "http_status": status,
            "content_type": content_type,
            "fetched_at": now,
            "accessed_at": now,
        }
    )
    return FetchResult(payload=payload)
