"""Smoke-test the backend without running a frontend or browser."""

from __future__ import annotations

import base64
import json
import os
import tempfile
from io import BytesIO
from pathlib import Path

try:
    from .app import create_app
except ImportError:  # Allows running ``python smoke_test.py`` inside backend.
    from app import create_app


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def main() -> None:
    os.environ["AKSARA_MOCK"] = "1"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(root / "vocab.db"),
                "AUDIO_DIR": str(root / "audio"),
            }
        )
        client = app.test_client()

        missing = client.post("/api/recognize")
        assert missing.status_code == 400, missing.json

        valid = client.post(
            "/api/recognize",
            data={"image": (BytesIO(PNG_1X1), "line.png")},
            content_type="multipart/form-data",
        )
        assert valid.status_code == 200, valid.json
        assert valid.json["success"] is True, valid.json
        assert "aksara" in valid.json
        assert "latin" in valid.json
        assert "character_details" in valid.json
        print("Smoke test passed")
        print(json.dumps(valid.json, ensure_ascii=True))


if __name__ == "__main__":
    main()

