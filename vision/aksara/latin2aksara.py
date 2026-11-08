"""Konverter Latin -> Aksara Sunda (aturan dasar, HANYA untuk pembuatan data/label).

Konvensi masukan: 'é' = taling, 'e' = pepet, 'eu' = eu. Bukan transliterator produksi
(itu tugas B, arah sebaliknya: Aksara -> Latin). Hasil perlu diverifikasi manual
untuk plang dengan ejaan tidak baku.
"""
KONSONAN = {
    "ng": "ᮍ", "ny": "ᮑ", "kh": "ᮮ", "sy": "ᮯ",
    "k": "ᮊ", "g": "ᮌ", "c": "ᮎ", "j": "ᮏ", "t": "ᮒ", "d": "ᮓ", "n": "ᮔ",
    "p": "ᮕ", "b": "ᮘ", "m": "ᮙ", "y": "ᮚ", "r": "ᮛ", "l": "ᮜ", "w": "ᮝ",
    "s": "ᮞ", "h": "ᮠ", "f": "ᮖ", "v": "ᮗ", "q": "ᮋ", "z": "ᮐ", "x": "ᮟ",
}
TANDA_AKHIR = {"ng": "ᮀ", "r": "ᮁ", "h": "ᮂ"}
MEDIAL = {"r": "ᮢ", "l": "ᮣ", "y": "ᮡ"}
VOKAL_MARK = {"a": "", "i": "ᮤ", "u": "ᮥ", "é": "ᮦ", "o": "ᮧ", "e": "ᮨ", "eu": "ᮩ"}
VOKAL_MANDIRI = {"a": "ᮃ", "i": "ᮄ", "u": "ᮅ", "é": "ᮆ", "o": "ᮇ", "e": "ᮈ", "eu": "ᮉ"}
PAMAEH = "᮪"


def _tokenize(word: str):
    w, i, out = word.lower(), 0, []
    while i < len(w):
        if w[i:i + 2] == "eu":
            out.append(("V", "eu")); i += 2
        elif w[i:i + 2] in ("ng", "ny", "kh", "sy"):
            out.append(("C", w[i:i + 2])); i += 2
        elif w[i] in VOKAL_MARK:
            out.append(("V", w[i])); i += 1
        elif w[i] in KONSONAN:
            out.append(("C", w[i])); i += 1
        else:
            i += 1  # abaikan karakter lain
    return out


def latin_to_aksara(text: str) -> str:
    hasil = []
    for word in text.split():
        t, i, buf, prev_vowel = _tokenize(word), 0, [], False
        first = True
        while i < len(t):
            kind, val = t[i]
            if kind == "V":
                buf.append(VOKAL_MANDIRI[val]); prev_vowel = True; i += 1
                continue
            nxt = t[i + 1] if i + 1 < len(t) else None
            nxt2 = t[i + 2] if i + 2 < len(t) else None
            if nxt and nxt[0] == "V":                      # KV
                buf.append(KONSONAN[val] + VOKAL_MARK[nxt[1]]); i += 2
            elif (nxt and nxt[0] == "C" and nxt[1] in MEDIAL and nxt2 and nxt2[0] == "V"
                  and val not in ("ng", "ny")):            # KKV medial (br-, kl-, ky-)
                buf.append(KONSONAN[val] + MEDIAL[nxt[1]] + VOKAL_MARK[nxt2[1]]); i += 3
            else:                                          # konsonan akhir / gugus
                if val in TANDA_AKHIR and buf:
                    buf.append(TANDA_AKHIR[val])
                else:
                    buf.append(KONSONAN[val] + PAMAEH)
                i += 1
            prev_vowel = False
            first = False
        hasil.append("".join(buf))
    return " ".join(hasil)


if __name__ == "__main__":
    for s in ["braga", "bandung", "dipatiukur", "asia afrika", "cihampelas", "cikapundung", "wilujeng sumping"]:
        print(f"{s:20s} -> {latin_to_aksara(s)}")
