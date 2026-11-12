"""Create the local vocabulary database and insert starter records."""

from pathlib import Path

try:
    from .db import connect
except ImportError:  # pragma: no cover - exercised by direct execution
    from db import connect

try:
    from aksara.latin2aksara import latin_to_aksara
except ImportError:  # pragma: no cover - direct execution without vision on path
    latin_to_aksara = lambda word: word


ROOT = Path(__file__).resolve().parent


COMMON_WORDS = {
    "imah": "Rumah",
    "cai": "Air",
    "dahar": "Makan",
    "sare": "Tidur",
    "hadé": "Baik atau bagus",
    "geulis": "Cantik atau indah",
    "wilujeng": "Selamat",
    "hatur nuhun": "Terima kasih",
}

BANDUNG_PLACES = {
    "braga": "Nama kawasan di Bandung",
    "asia afrika": "Nama jalan di Kota Bandung",
    "dago": "Nama kawasan dan jalan di Bandung",
    "riau": "Nama jalan di Kota Bandung",
    "cihampelas": "Nama jalan di Kota Bandung",
    "dipatiukur": "Nama jalan di Kota Bandung",
    "pasteur": "Nama kawasan dan jalan di Bandung",
    "setiabudi": "Nama jalan di Kota Bandung",
    "merdeka": "Nama jalan di Kota Bandung",
    "surapati": "Nama jalan di Kota Bandung",
    "pasirkaliki": "Nama jalan di Kota Bandung",
    "otto iskandardinata": "Nama jalan di Kota Bandung",
    "ahmad yani": "Nama jalan di Kota Bandung",
    "soekarno hatta": "Nama jalan di Kota Bandung",
    "wastu kencana": "Nama jalan di Kota Bandung",
    "pajajaran": "Nama jalan di Kota Bandung",
    "naripan": "Nama jalan di Kota Bandung",
}


def records() -> list[tuple[str, str, str, str | None, str]]:
    entries = {**COMMON_WORDS, **BANDUNG_PLACES}
    return [(latin_to_aksara(latin), latin, meaning, None, "local") for latin, meaning in entries.items()]


def main() -> None:
    with connect(ROOT / "data" / "vocab.db") as connection:
        connection.executemany(
            """
            INSERT INTO vocabulary (aksara, latin, meaning, audio_file, source)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(aksara) DO UPDATE SET
                latin = excluded.latin,
                meaning = excluded.meaning,
                audio_file = excluded.audio_file,
                source = 'local'
            """,
            records(),
        )
    print("Vocabulary database ready")


if __name__ == "__main__":
    main()

