"""Rule-based transliteration from Sundanese Unicode script to Latin."""

from __future__ import annotations

from dataclasses import dataclass


SWARA = {
    "\u1b83": "a", "\u1b84": "i", "\u1b85": "u", "\u1b86": "é",
    "\u1b87": "o", "\u1b88": "e", "\u1b89": "eu",
}

NGALAGENA = {
    "\u1b8a": "k", "\u1b8c": "g", "\u1b8d": "ng", "\u1b8e": "c",
    "\u1b8f": "j", "\u1b91": "ny", "\u1b92": "t", "\u1b93": "d",
    "\u1b94": "n", "\u1b95": "p", "\u1b98": "b", "\u1b99": "m",
    "\u1b9a": "y", "\u1b9b": "r", "\u1b9c": "l", "\u1b9d": "w",
    "\u1b9e": "s", "\u1ba0": "h",
    "\u1b8b": "q", "\u1b90": "z", "\u1b96": "f", "\u1b97": "v",
    "\u1b9f": "x", "\u1bae": "kh", "\u1baf": "sy",
}

VOWEL_MARKS = {
    "\u1ba4": "i", "\u1ba5": "u", "\u1ba6": "é", "\u1ba7": "o",
    "\u1ba8": "e", "\u1ba9": "eu",
}
MEDIAL_MARKS = {"\u1ba1": "y", "\u1ba2": "r", "\u1ba3": "l"}
FINAL_SIGNS = {"\u1b80": "ng", "\u1b81": "r", "\u1b82": "h"}
PAMAEH = "\u1baa"


@dataclass(frozen=True)
class Transliteration:
    latin: str
    chars: list[dict[str, str]]


def _learning_detail(cluster: str, latin: str, note: str) -> dict[str, str]:
    """Build learner-facing metadata for one aksara cluster."""
    if any(mark in cluster for mark in VOWEL_MARKS):
        category = "Aksara dengan rarangkén vokal"
    elif any(mark in cluster for mark in MEDIAL_MARKS):
        category = "Aksara dengan rarangkén medial"
    elif any(mark in cluster for mark in FINAL_SIGNS):
        category = "Aksara dengan tanda akhir"
    elif PAMAEH in cluster:
        category = "Aksara dengan pamaéh"
    elif cluster in SWARA:
        category = "Aksara swara"
    else:
        category = "Aksara ngalagena"
    return {
        "category": category,
        "explanation": f"Gugus ini dibaca '{latin}'. Aturan pembentuk: {note}.",
    }


def transliterate(text: str) -> Transliteration:
    """Transliterate one Unicode Sundanese string and explain each cluster."""
    output: list[str] = []
    chars: list[dict[str, str]] = []
    i = 0
    while i < len(text):
        glyph = text[i]
        if glyph.isspace():
            output.append(" ")
            i += 1
            continue
        if glyph in SWARA:
            latin = SWARA[glyph]
            detail = _learning_detail(glyph, latin, "swara")
            chars.append({"glyph": glyph, "latin": latin, "note": "swara", **detail})
            output.append(latin)
            i += 1
            continue
        if glyph not in NGALAGENA:
            # Preserve unknown characters instead of silently dropping OCR output.
            chars.append({
                "glyph": glyph,
                "latin": glyph,
                "note": "karakter belum dipetakan",
                "category": "Karakter belum dipetakan",
                "explanation": "Karakter ini belum memiliki aturan transliterasi.",
            })
            output.append(glyph)
            i += 1
            continue

        cluster = glyph
        latin = NGALAGENA[glyph]
        vowel = "a"
        suffix = ""
        note = "ngalagena"
        i += 1
        marks = set(VOWEL_MARKS) | set(MEDIAL_MARKS) | set(FINAL_SIGNS) | {PAMAEH}
        while i < len(text) and text[i] in marks:
            mark = text[i]
            cluster += mark
            if mark in VOWEL_MARKS:
                vowel = VOWEL_MARKS[mark]
                note += " + vokal " + vowel
            elif mark in MEDIAL_MARKS:
                latin += MEDIAL_MARKS[mark]
                note += " + medial " + MEDIAL_MARKS[mark]
            elif mark in FINAL_SIGNS:
                suffix += FINAL_SIGNS[mark]
                note += " + tanda akhir " + FINAL_SIGNS[mark]
            else:
                vowel = ""
                note += " + pamaéh"
            i += 1
        result = latin + vowel + suffix
        output.append(result)
        chars.append({"glyph": cluster, "latin": result, "note": note, **_learning_detail(cluster, result, note)})
    return Transliteration("".join(output), chars)

