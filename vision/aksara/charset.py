"""Inventaris karakter Aksara Sunda (Unicode U+1B80-U+1BBF) + metrik CER.

Token model = codepoint Unicode. Indeks 0 dicadangkan untuk blank CTC.
"""
import unicodedata

# Aksara Sunda Baku
SWARA = "ᮃᮄᮅᮆᮇᮈᮉ"                       # a i u é o e eu
NGALAGENA = "ᮊᮌᮍᮎᮏᮑᮒᮓᮔᮕᮘᮙᮚᮛᮜᮝᮞᮠ"      # ka ga nga ca ja nya ta da na pa ba ma ya ra la wa sa ha
NGALAGENA_TAMBAHAN = "ᮋᮐᮖᮗᮟᮮᮯ"            # qa za fa va xa kha sya (serapan)
# Rarangkén
SIGN_AKHIR = "ᮀᮁᮂ"                        # panyecek(ng) panglayar(r) pangwisad(h)
MEDIAL = "ᮡᮢᮣ"                            # pamingkal(-ya) panyakra(-ra) panyiku(-la)
VOKAL = "ᮤᮥᮦᮧᮨᮩ"                         # i u é o e eu
PAMAEH = "᮪"                              # mematikan vokal inheren
DIGITS = "᮰᮱᮲᮳᮴᮵᮶᮷᮸᮹"
OTHER = "ᮺᮻᮼᮽᮾᮿᮬᮭ᮫"

BLANK = "<blank>"
SPACE = " "

_chars = (SWARA + NGALAGENA + NGALAGENA_TAMBAHAN + SIGN_AKHIR + MEDIAL + VOKAL
          + PAMAEH + DIGITS + OTHER)
VOCAB = [BLANK, SPACE] + sorted(set(_chars))
CHAR2ID = {c: i for i, c in enumerate(VOCAB)}
ID2CHAR = {i: c for c, i in CHAR2ID.items()}
NUM_CLASSES = len(VOCAB)


def encode(text: str):
    return [CHAR2ID[c] for c in text if c in CHAR2ID]


def decode_ids(ids):
    return "".join(ID2CHAR[i] for i in ids if i != 0)


def is_sundanese(text: str) -> bool:
    return all(0x1B80 <= ord(c) <= 0x1BBF or c == SPACE for c in text)


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(refs, hyps) -> float:
    """Character Error Rate pada string Unicode (total edit / total panjang ref)."""
    edits = sum(levenshtein(r, h) for r, h in zip(refs, hyps))
    total = sum(len(r) for r in refs)
    return edits / max(total, 1)


def word_accuracy(refs, hyps) -> float:
    return sum(r == h for r, h in zip(refs, hyps)) / max(len(refs), 1)


if __name__ == "__main__":
    print("jumlah kelas (termasuk blank & spasi):", NUM_CLASSES)
    for c in VOCAB[2:]:
        print(f"U+{ord(c):04X} {c} {unicodedata.name(c)}")
