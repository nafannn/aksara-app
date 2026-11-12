"""SQLite storage and fuzzy lookup for the AKSARA vocabulary."""

from __future__ import annotations

import sqlite3
from difflib import SequenceMatcher
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aksara TEXT NOT NULL UNIQUE,
    latin TEXT NOT NULL,
    meaning TEXT,
    audio_file TEXT,
    source TEXT NOT NULL DEFAULT 'local'
)
"""


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(SCHEMA)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(vocabulary)")}
    if "source" not in columns:
        connection.execute(
            "ALTER TABLE vocabulary ADD COLUMN source TEXT NOT NULL DEFAULT 'local'"
        )
        connection.commit()
    return connection


def find_word(connection: sqlite3.Connection, aksara: str, latin: str) -> dict | None:
    row = connection.execute(
        "SELECT aksara, latin, meaning, audio_file, source FROM vocabulary WHERE aksara = ? OR lower(latin) = lower(?)",
        (aksara, latin),
    ).fetchone()
    if row:
        return dict(row)

    candidates = connection.execute(
        "SELECT aksara, latin, meaning, audio_file, source FROM vocabulary"
    ).fetchall()
    best = None
    best_score = 0.0
    for candidate in candidates:
        score = SequenceMatcher(None, latin.lower(), candidate["latin"].lower()).ratio()
        if score > best_score:
            best, best_score = dict(candidate), score
    return best if best_score >= 0.75 else None

