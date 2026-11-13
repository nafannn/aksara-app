import base64
from io import BytesIO

from app import create_app


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def make_client(tmp_path):
    return create_app(
        {"TESTING": True, "DATABASE": str(tmp_path / "vocab.db"), "AUDIO_DIR": str(tmp_path)}
    ).test_client()


def post_image(client, data=PNG_1X1, name="line.png", mimetype="image/png"):
    return client.post(
        "/api/recognize",
        data={"image": (BytesIO(data), name, mimetype)},
        content_type="multipart/form-data",
    )


def test_missing_image_returns_400(tmp_path):
    response = make_client(tmp_path).post("/api/recognize")
    assert response.status_code == 400
    assert response.json["success"] is False
    assert "message" in response.json


def test_unsupported_type_returns_415(tmp_path):
    response = post_image(make_client(tmp_path), data=b"halo", name="a.txt", mimetype="text/plain")
    assert response.status_code == 415
    assert response.json["success"] is False


def test_invalid_image_returns_400(tmp_path):
    response = post_image(make_client(tmp_path), data=b"bukan gambar")
    assert response.status_code == 400
    assert response.json["success"] is False


def test_mock_recognition_follows_frontend_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("AKSARA_MOCK", "1")
    response = post_image(make_client(tmp_path))
    assert response.status_code == 200
    body = response.json
    assert body["success"] is True
    assert body["aksara"]
    assert "latin" in body and "meaning" in body and "audio_url" in body
    assert body["character_details"], "character_details tidak boleh kosong"
    for item in body["character_details"]:
        assert set(item) == {"aksara", "reading", "category", "explanation"}
    assert "status" not in body and "chars" not in body


def test_unrecognized_returns_200_with_success_false(tmp_path, monkeypatch):
    import aksara.recognize as recognizer

    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "", "confidence": 0.0})
    response = post_image(make_client(tmp_path))
    assert response.status_code == 200
    assert response.json["success"] is False
    assert response.json["aksara"] == ""
    assert response.json["character_details"] == []
