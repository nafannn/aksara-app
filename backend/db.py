"""SQLite storage and fuzzy lookup for the AKSARA vocabulary.

Lookup tidak pernah mengembalikan tebakan sebagai fakta: hasil cocok persis ditandai
``match="exact"``, hasil mirip ditandai ``match="fuzzy"`` beserta skornya, supaya
lapisan API bisa memberi tahu pengguna bahwa maknanya berasal dari kata terdekat.
"""

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

# Ambang kemiripan dan panjang minimum. Kata pendek ("bra", "cai") terlalu mudah
# berdekatan dengan kata lain, dan makna nama jalan yang salah lebih menyesatkan
# daripada tidak ada makna sama sekali.
FUZZY_THRESHOLD = 0.75
MIN_FUZZY_LENGTH = 4

_COLUMNS = "aksara, latin, meaning, audio_file, source"


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


def best_fuzzy_match(connection: sqlite3.Connection, latin: str) -> dict | None:
    """Kata kamus paling mirip dengan ``latin``, atau None bila di bawah ambang."""
    query = latin.strip().lower()
    if len(query) < MIN_FUZZY_LENGTH:
        return None
    best = None
    best_score = 0.0
    for candidate in connection.execute(f"SELECT {_COLUMNS} FROM vocabulary").fetchall():
        if len(candidate["latin"]) < MIN_FUZZY_LENGTH:
            continue
        score = SequenceMatcher(None, query, candidate["latin"].lower()).ratio()
        if score > best_score:
            best, best_score = dict(candidate), score
    if best is None or best_score < FUZZY_THRESHOLD:
        return None
    return {**best, "match": "fuzzy", "score": round(best_score, 3)}


def find_word(connection: sqlite3.Connection, aksara: str, latin: str) -> dict | None:
    """Cari entri kamus: persis dulu (aksara atau latin), lalu kemiripan latin.

    Hasil selalu punya ``match`` ("exact" atau "fuzzy") supaya pemanggil bisa
    membedakan makna pasti dari tebakan.
    """
    row = connection.execute(
        f"SELECT {_COLUMNS} FROM vocabulary WHERE aksara = ? OR lower(latin) = lower(?)",
        (aksara, latin),
    ).fetchone()
    if row:
        return {**dict(row), "match": "exact", "score": 1.0}
    return best_fuzzy_match(connection, latin)


def remember_audio(connection: sqlite3.Connection, aksara: str, audio_file: str) -> None:
    """Simpan nama berkas audio hasil sintesis agar permintaan berikutnya memakai cache."""
    connection.execute(
        "UPDATE vocabulary SET audio_file = ? WHERE aksara = ? AND (audio_file IS NULL OR audio_file != ?)",
        (audio_file, aksara, audio_file),
    )
    connection.commit()

