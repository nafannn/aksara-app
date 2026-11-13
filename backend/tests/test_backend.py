import base64
from io import BytesIO

from app import create_app


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def make_client(tmp_path, seed=()):
    """App uji tanpa jaringan: kunci API dikosongkan supaya tes tidak memanggil
    Google/APIPedia dan hasilnya deterministik."""
    from db import connect

    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "vocab.db"),
            "AUDIO_DIR": str(tmp_path),
            "APIPEDIA_API_KEY": "",
            "APIPEDIA_VOICE": "su-ID-TutiNeural",
            "GOOGLE_TRANSLATE_API_KEY": "",
            "GOOGLE_TRANSLATE_SCRIPT_URL": "",
            "TTS_TIMEOUT": 0.1,
        }
    )
    connection = connect(str(tmp_path / "vocab.db"))
    try:
        connection.executemany(
            "INSERT INTO vocabulary (aksara, latin, meaning, audio_file) VALUES (?, ?, ?, ?)",
            seed,
        )
        connection.commit()
    finally:
        connection.close()
    return app.test_client()


def post_image(client, data=PNG_1X1, name="line.png", mimetype="image/png"):
    return client.post(
        "/api/recognize",
        data={"image": (BytesIO(data), name, mimetype)},
        content_type="multipart/form-data",
    )


def test_healthz_reports_ok(tmp_path):
    response = make_client(tmp_path).get("/healthz")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


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


BRAGA = ("ᮘᮢᮌ", "braga", "Nama kawasan di Bandung", None)


def test_exact_kamus_match_is_labelled_kamus(tmp_path, monkeypatch):
    import aksara.recognize as recognizer

    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "ᮘᮢᮌ", "confidence": 0.9})
    body = post_image(make_client(tmp_path, seed=[BRAGA])).json
    assert body["meaning"] == "Nama kawasan di Bandung"
    assert body["meaning_source"] == "kamus"
    assert body["matched_latin"] is None


def test_fuzzy_match_is_labelled_mirip_and_names_the_candidate(tmp_path, monkeypatch):
    import aksara.recognize as recognizer

    # "brag" (bra + pamaéh) bukan kata di kamus, tapi mirip "braga".
    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "ᮘᮢᮌ᮪", "confidence": 0.9})
    body = post_image(make_client(tmp_path, seed=[BRAGA])).json
    assert body["latin"] == "brag"
    assert body["meaning"] == "Nama kawasan di Bandung"
    assert body["meaning_source"] == "mirip"
    assert body["matched_latin"] == "braga"


def test_short_single_cluster_shows_reading_not_a_dictionary_meaning(tmp_path, monkeypatch):
    import aksara.recognize as recognizer

    # "bra" hanya 3 huruf, tidak boleh dipaksa mirip nama jalan mana pun.
    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "ᮘᮢ", "confidence": 0.9})
    body = post_image(make_client(tmp_path, seed=[BRAGA])).json
    assert body["meaning"] == "bra"
    assert body["meaning_source"] == "bacaan"
    assert body["matched_latin"] is None


def test_bundled_audio_rescues_a_stale_cache_reference(tmp_path, monkeypatch):
    import aksara.recognize as recognizer
    from audio_service import cache_filename

    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "ᮘᮢᮌ", "confidence": 0.9})
    stale = ("ᮘᮢᮌ", "braga", "Nama kawasan di Bandung", "tts_hilang.mp3")
    client = make_client(tmp_path, seed=[stale])
    body = post_image(client).json
    assert body["success"] is True
    # Berkas lama hilang, tetapi audio bawaan (backend/audio_seed) menutupinya.
    assert body["audio_url"] == f"/audio/{cache_filename('braga')}"
    assert (tmp_path / cache_filename("braga")).is_file()


def test_audio_url_is_null_when_no_audio_can_be_produced(tmp_path, monkeypatch):
    import aksara.recognize as recognizer

    # Tidak ada kunci APIPedia dan kata ini tidak punya audio bawaan.
    monkeypatch.setattr(recognizer, "recognize", lambda image: {"aksara": "ᮞᮥᮛᮒ᮪", "confidence": 0.9})
    body = post_image(make_client(tmp_path, seed=[BRAGA])).json
    assert body["success"] is True
    assert body["audio_url"] is None


def test_best_fuzzy_match_skips_short_and_distant_words(tmp_path):
    from db import best_fuzzy_match, connect, find_word

    connection = connect(tmp_path / "vocab.db")
    try:
        connection.execute(
            "INSERT INTO vocabulary (aksara, latin, meaning) VALUES (?, ?, ?)", BRAGA[:3]
        )
        connection.commit()
        assert find_word(connection, "ᮘᮢᮌ", "braga")["match"] == "exact"
        fuzzy = best_fuzzy_match(connection, "brag")
        assert fuzzy is not None and fuzzy["match"] == "fuzzy"
        assert best_fuzzy_match(connection, "bra") is None
        assert best_fuzzy_match(connection, "xyzzy") is None
    finally:
        connection.close()
