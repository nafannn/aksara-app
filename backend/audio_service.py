"""APIPedia TTS integration with a local MP3 cache."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


APIPEDIA_TTS_URL = "https://api.apipedia.id/v1/tts"
MAX_TEXT_LENGTH = 5000


def synthesize_audio(
    text: str,
    audio_dir: str | Path,
    api_key: str | None,
    voice: str = "su-ID-TutiNeural",
    timeout: float = 5.0,
) -> str | None:
    """Generate and cache one Sundanese MP3, returning its filename."""
    normalized = text.strip()
    if not normalized or not api_key or len(normalized) > MAX_TEXT_LENGTH:
        return None

    destination_dir = Path(audio_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(f"{voice}\0{normalized}".encode("utf-8")).hexdigest()[:20]
    filename = f"tts_{cache_key}.mp3"
    destination = destination_dir / filename
    if destination.exists() and destination.stat().st_size > 0:
        return filename

    payload = json.dumps({"text": normalized, "voice": voice, "bitrate": 96}).encode("utf-8")
    request = Request(
        f"{APIPEDIA_TTS_URL}?output=audio&server=1",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "User-Agent": "AKSARA-backend/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            audio = response.read()
    except (HTTPError, URLError, TimeoutError, OSError):
        return None

    if content_type == "application/json" or not audio:
        return None

    temporary = destination.with_suffix(".part")
    temporary.write_bytes(audio)
    temporary.replace(destination)
    return filename
