"""Flask API for recognizing, transliterating, and looking up Aksara Sunda."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:  # Supports both ``python -m backend.app`` and local test execution.
    from .audio_service import synthesize_audio
    from .db import connect, find_word
    from .google_translate import translate_sundanese_to_indonesian
    from .translator import transliterate
except ImportError:  # pragma: no cover - exercised by the local runner
    from audio_service import synthesize_audio
    from db import connect, find_word
    from google_translate import translate_sundanese_to_indonesian
    from translator import transliterate


DEFAULT_MAX_BYTES = 8 * 1024 * 1024


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
        AUDIO_DIR=str(root / "audio"),
        APIPEDIA_API_KEY=os.getenv("APIPEDIA_API_KEY", ""),
        APIPEDIA_VOICE=os.getenv("APIPEDIA_VOICE", "su-ID-TutiNeural"),
        GOOGLE_TRANSLATE_SCRIPT_URL=os.getenv("GOOGLE_TRANSLATE_SCRIPT_URL", ""),
        GOOGLE_TRANSLATE_API_KEY=os.getenv("GOOGLE_TRANSLATE_API_KEY", ""),
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
    Path(app.config["AUDIO_DIR"]).mkdir(parents=True, exist_ok=True)

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(status="error", message="Berkas terlalu besar"), 413

    @app.post("/api/recognize")
    def recognize_endpoint():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return jsonify(status="error", message="Field image wajib diisi"), 400
        if uploaded.mimetype not in {"image/jpeg", "image/png"}:
            return jsonify(status="error", message="Tipe gambar harus JPEG atau PNG"), 415

        data = uploaded.read()
        try:
            import cv2
            import numpy as np
            image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        except ImportError:
            return jsonify(status="error", message="Dependensi image processing belum terpasang"), 500
        if image is None:
            return jsonify(status="error", message="Berkas bukan gambar yang valid"), 400

        try:
            from aksara.recognize import recognize
            result = recognize(image)
        except Exception:
            app.logger.exception("recognition failed")
            return jsonify(status="error", message="Gagal memproses gambar"), 500

        aksara = result.get("aksara", "")
        confidence = float(result.get("confidence", 0.0))
        if not aksara.strip():
            return jsonify(status="unrecognized", aksara="", latin="", chars=[], meaning=None, audio_url=None, confidence=confidence)

        translated = transliterate(aksara)
        connection = connect(app.config["DATABASE"])
        try:
            word = find_word(connection, aksara, translated.latin)
        finally:
            connection.close()
        meaning = word.get("meaning") if word else None
        google_key = app.config["GOOGLE_TRANSLATE_API_KEY"]
        google_script_url = app.config["GOOGLE_TRANSLATE_SCRIPT_URL"]
        is_single_aksara = len(translated.chars) <= 1
        if not word and not is_single_aksara:
            meaning = (
                translate_sundanese_to_indonesian(
                    translated.latin,
                    google_key,
                    google_script_url,
                )
                or meaning
            )
        if is_single_aksara and not meaning:
            meaning = translated.latin
        audio_file = word.get("audio_file") if word else None
        if not audio_file:
            audio_file = synthesize_audio(
                translated.latin,
                app.config["AUDIO_DIR"],
                app.config["APIPEDIA_API_KEY"],
                app.config["APIPEDIA_VOICE"],
            )
        audio_url = f"/audio/{audio_file}" if audio_file else None
        return jsonify(
            status="ok" if word else "not_found",
            aksara=aksara,
            latin=translated.latin,
            confidence=confidence,
            chars=translated.chars,
            meaning=meaning,
            audio_url=audio_url,
        )

    @app.get("/audio/<path:filename>")
    def audio(filename: str):
        return send_from_directory(app.config["AUDIO_DIR"], filename)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)

