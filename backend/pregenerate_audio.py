"""Isi cache audio untuk semua kata di kamus lokal.

Audio TTS diberi nama deterministik (sha256 dari voice + teks), jadi selama folder
cache-nya persisten, tautan ``/audio/<berkas>`` tetap hidup setelah backend restart.
Jalankan skrip ini sekali saat deploy (atau setelah menambah kata ke ``seed.py``):

    AKSARA_AUDIO_DIR=/data/aksara-audio python -m backend.pregenerate_audio

Tanpa API key, skrip hanya melapor dan keluar tanpa mengubah apa pun.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

try:
    from .app import load_env_file
    from .audio_service import synthesize_audio
    from .db import connect, remember_audio
except ImportError:  # pragma: no cover - direct execution inside backend/
    from app import load_env_file
    from audio_service import synthesize_audio
    from db import connect, remember_audio


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(ROOT / "data" / "vocab.db"))
    parser.add_argument("--audio-dir", default=os.getenv("AKSARA_AUDIO_DIR", str(ROOT / "audio")))
    parser.add_argument("--voice", default=os.getenv("APIPEDIA_VOICE", "su-ID-TutiNeural"))
    parser.add_argument("--force", action="store_true", help="sintesis ulang walau berkas sudah ada")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    api_key = os.getenv("APIPEDIA_API_KEY", "")
    if not api_key:
        print("APIPEDIA_API_KEY kosong: tidak ada audio yang dibuat.")
        return 1

    audio_dir = Path(args.audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    created, cached, failed = 0, 0, 0
    connection = connect(args.db)
    try:
        rows = connection.execute(
            "SELECT aksara, latin, audio_file FROM vocabulary ORDER BY latin"
        ).fetchall()
        for row in rows:
            existing = row["audio_file"]
            if not args.force and existing and (audio_dir / existing).is_file():
                cached += 1
                continue
            filename = synthesize_audio(row["latin"], audio_dir, api_key, args.voice)
            if filename:
                remember_audio(connection, row["aksara"], filename)
                created += 1
                print(f"ok   {row['latin']:24s} -> {filename}")
            else:
                failed += 1
                print(f"gagal {row['latin']}")
    finally:
        connection.close()

    print(
        f"\n{len(rows)} kata: {created} dibuat, {cached} sudah ada, {failed} gagal."
        f"\nFolder cache: {audio_dir}"
    )
    if failed and not created:
        print("Semua gagal: periksa koneksi internet dan validitas APIPEDIA_API_KEY.")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
