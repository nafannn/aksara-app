import base64
import sqlite3

from app import create_app


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_missing_image_returns_400(tmp_path):
    client = create_app({"TESTING": True, "DATABASE": str(tmp_path / "vocab.db"), "AUDIO_DIR": str(tmp_path)}).test_client()
    response = client.post("/api/recognize")
    assert response.status_code == 400


def test_mock_recognition_returns_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("AKSARA_MOCK", "1")
    client = create_app({"TESTING": True, "DATABASE": str(tmp_path / "vocab.db"), "AUDIO_DIR": str(tmp_path)}).test_client()
    response = client.post("/api/recognize", data={"image": (io_bytes(), "line.png")}, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.json["status"] in {"ok", "not_found"}
    assert "latin" in response.json


def io_bytes():
    from io import BytesIO
    return BytesIO(PNG_1X1)

