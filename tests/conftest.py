from __future__ import annotations

from pathlib import Path

import pytest

from app.db import Database


@pytest.fixture
def database(tmp_path: Path) -> Database:
    db = Database(tmp_path / "test.sqlite3")
    db.initialize()
    return db
