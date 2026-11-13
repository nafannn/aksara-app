"""Flask API for recognizing, transliterating, and looking up Aksara Sunda."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:  # Supports both ``python -m backend.app`` and local test execution.
    from .audio_service import synthesize_audio
    from .db import connect, find_word, remember_audio
    from .google_translate import translate_sundanese_to_indonesian
    from .translator import transliterate
except ImportError:  # pragma: no cover - exercised by the local runner
    from audio_service import synthesize_audio
    from db import connect, find_word, remember_audio
    from google_translate import translate_sundanese_to_indonesian
    from translator import transliterate


DEFAULT_MAX_BYTES = 8 * 1024 * 1024

# Modul pengenalan (`aksara`) ada di ../vision. Dengan ini PYTHONPATH tidak wajib diatur manual.
_VISION_DIR = Path(__file__).resolve().parent.parent / "vision"
if _VISION_DIR.is_dir() and str(_VISION_DIR) not in sys.path:
    sys.path.insert(0, str(_VISION_DIR))


def writable_dir(preferred: Path) -> Path:
    """Folder untuk cache audio. Jika folder pilihan tidak bisa ditulis (mis. filesystem
    read-only di serverless), pakai folder sementara."""
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_test"
        probe.write_bytes(b"")
        probe.unlink()
        return preferred
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "aksara_audio"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def character_details(chars: list[dict]) -> list[dict]:
    """Ubah keluaran transliterator ke bentuk yang dibaca frontend (kontrak v0.3)."""
    return [
        {
            "aksara": item.get("glyph", ""),
            "reading": item.get("latin", ""),
            "category": item.get("category", ""),
            "explanation": item.get("explanation", ""),
        }
        for item in chars
    ]


def resolve_meaning(
    word: dict | None,
    latin: str,
    is_single_cluster: bool,
    google_key: str,
    google_script_url: str,
) -> tuple[str | None, str | None, str | None]:
    """Tentukan makna beserta asalnya: kamus, mirip, terjemahan, atau bacaan.

    ``mirip`` wajib dibedakan dari ``kamus``: tebakan kemiripan tidak boleh
    tampil sebagai makna pasti ("aksara ini berarti nama jalan X").
    """
    if word and word.get("meaning"):
        exact = word.get("match") == "exact"
        return word["meaning"], ("kamus" if exact else "mirip"), (None if exact else word.get("latin"))
    if is_single_cluster:
        # Satu gugus: tidak ada kata yang bisa dicari, jadi tampilkan bacaannya saja.
        return latin, "bacaan", None
    translated = translate_sundanese_to_indonesian(latin, google_key, google_script_url)
    return (translated, "terjemahan", None) if translated else (None, None, None)


def cached_audio(filename: str | None, audio_dir: str) -> str | None:
    """Nama berkas audio yang benar-benar ada di disk (tautan mati => None)."""
    if not filename:
        return None
    path = Path(audio_dir) / Path(filename).name
    return path.name if path.is_file() and path.stat().st_size > 0 else None


def load_env_file(path: Path) -> None:
    """Load simple KEY=value settings without overriding real environment vars."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    root = Path(__file__).resolve().parent
    load_env_file(root / ".env")
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=int(os.getenv("AKSARA_MAX_UPLOAD_BYTES", DEFAULT_MAX_BYTES)),
        DATABASE=str(root / "data" / "vocab.db"),
        AUDIO_DIR=os.getenv("AKSARA_AUDIO_DIR", str(root / "audio")),
        APIPEDIA_API_KEY=os.getenv("APIPEDIA_API_KEY", ""),
        APIPEDIA_VOICE=os.getenv("APIPEDIA_VOICE", "su-ID-TutiNeural"),
        GOOGLE_TRANSLATE_SCRIPT_URL=os.getenv("GOOGLE_TRANSLATE_SCRIPT_URL", ""),
        GOOGLE_TRANSLATE_API_KEY=os.getenv("GOOGLE_TRANSLATE_API_KEY", ""),
        TTS_TIMEOUT=float(os.getenv("AKSARA_TTS_TIMEOUT", "5")),
    )
    if test_config:
        app.config.update(test_config)

    @app.after_request
    def add_cors_headers(response):
        # Development-friendly default; set AKSARA_CORS_ORIGIN explicitly in deployment.
        allowed_origin = os.getenv("AKSARA_CORS_ORIGIN", "*")
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.config["AUDIO_DIR"] = str(writable_dir(Path(app.config["AUDIO_DIR"])))

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(success=False, message="Berkas terlalu besar"), 413

    @app.post("/api/recognize")
    def recognize_endpoint():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return jsonify(success=False, message="Field image wajib diisi"), 400
        if uploaded.mimetype not in {"image/jpeg", "image/png"}:
            return jsonify(success=False, message="Tipe gambar harus JPEG atau PNG"), 415

        data = uploaded.read()
        try:
            import cv2
            import numpy as np
            image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        except ImportError:
            return jsonify(success=False, message="Dependensi image processing belum terpasang"), 500
        if image is None:
            return jsonify(success=False, message="Berkas bukan gambar yang valid"), 400

        try:
            from aksara.recognize import recognize
            result = recognize(image)
        except Exception:
            app.logger.exception("recognition failed")
            return jsonify(success=False, message="Gagal memproses gambar"), 500

        aksara = result.get("aksara", "")
        confidence = float(result.get("confidence", 0.0))
        if not aksara.strip():
            return jsonify(
                success=False,
                aksara="",
                latin=None,
                meaning=None,
                meaning_source=None,
                matched_latin=None,
                audio_url=None,
                character_details=[],
                confidence=confidence,
            )

        translated = transliterate(aksara)
        connection = connect(app.config["DATABASE"])
        try:
            word = find_word(connection, aksara, translated.latin)
            meaning, meaning_source, matched_latin = resolve_meaning(
                word,
                translated.latin,
                len(translated.chars) <= 1,
                app.config["GOOGLE_TRANSLATE_API_KEY"],
                app.config["GOOGLE_TRANSLATE_SCRIPT_URL"],
            )
            audio_file = cached_audio(
                word.get("audio_file") if word else None, app.config["AUDIO_DIR"]
            )
            if not audio_file:
                audio_file = synthesize_audio(
                    translated.latin,
                    app.config["AUDIO_DIR"],
                    app.config["APIPEDIA_API_KEY"],
                    app.config["APIPEDIA_VOICE"],
                    timeout=app.config["TTS_TIMEOUT"],
                )
                # Simpan nama berkasnya supaya permintaan berikutnya tidak memanggil TTS lagi.
                if audio_file and word:
                    remember_audio(connection, aksara, audio_file)
        finally:
            connection.close()
        audio_url = f"/audio/{audio_file}" if audio_file else None
        return jsonify(
            success=True,
            aksara=aksara,
            latin=translated.latin,
            meaning=meaning,
            meaning_source=meaning_source,
            matched_latin=matched_latin,
            audio_url=audio_url,
            character_details=character_details(translated.chars),
            confidence=confidence,
        )

    @app.get("/audio/<path:filename>")
    def audio(filename: str):
        return send_from_directory(app.config["AUDIO_DIR"], filename)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)

