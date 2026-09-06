from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_path: Path
    max_fetch_bytes: int
    max_extract_chars: int
    request_timeout_seconds: float
    max_redirects: int
    allow_private_fetch: bool
    respect_robots_txt: bool
    user_agent: str


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    data_dir = Path(os.getenv("GORECLOUD_RESEARCH_DATA_DIR", "./data")).expanduser().resolve()
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "research-library.sqlite3",
        max_fetch_bytes=int(os.getenv("GORECLOUD_RESEARCH_MAX_FETCH_BYTES", str(5 * 1024 * 1024))),
        max_extract_chars=int(os.getenv("GORECLOUD_RESEARCH_MAX_EXTRACT_CHARS", "250000")),
        request_timeout_seconds=float(os.getenv("GORECLOUD_RESEARCH_TIMEOUT_SECONDS", "20")),
        max_redirects=int(os.getenv("GORECLOUD_RESEARCH_MAX_REDIRECTS", "5")),
        allow_private_fetch=_env_bool("GORECLOUD_RESEARCH_ALLOW_PRIVATE_FETCH", False),
        respect_robots_txt=_env_bool("GORECLOUD_RESEARCH_RESPECT_ROBOTS", True),
        user_agent=os.getenv(
            "GORECLOUD_RESEARCH_USER_AGENT",
            "GoreeCloudResearchLibrary/0.1 (+https://github.com/GoreeCloud/goreecloud-research-library)",
        ),
    )


settings = load_settings()
