"""Small Google Cloud Translation Basic v2 client for meaning lookup."""

from __future__ import annotations

import html
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


def translate_via_script(
    text: str,
    script_url: str | None,
    timeout: float = 15.0,
) -> str | None:
    """Call the project's public Google Apps Script translation endpoint."""
    if not text.strip() or not script_url:
        return None

    payload = json.dumps({"text": text.strip()}).encode("utf-8")
    request = Request(
        script_url,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AKSARA-backend/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    if not data.get("success"):
        return None
    translation = data.get("translation")
    return html.unescape(str(translation)).strip() if translation else None


def translate_sundanese_to_indonesian(
    text: str,
    api_key: str | None,
    script_url: str | None = None,
    timeout: float = 15.0,
) -> str | None:
    """Translate one Sundanese phrase, returning None when Google is unavailable."""
    script_translation = translate_via_script(text, script_url, timeout)
    if script_translation:
        return script_translation
    if not text.strip() or not api_key:
        return None

    payload = json.dumps(
        {
            "q": text.strip(),
            "source": "su",
            "target": "id",
            "format": "text",
        }
    ).encode("utf-8")
    url = f"{TRANSLATE_URL}?{urlencode({'key': api_key})}"
    request = Request(
        url,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AKSARA-backend/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    translations = data.get("data", {}).get("translations", [])
    if not translations:
        return None
    translated = translations[0].get("translatedText")
    return html.unescape(translated).strip() if translated else None
