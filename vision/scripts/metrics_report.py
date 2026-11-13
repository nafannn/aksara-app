"""Laporan metrik pengenalan baris teks: CER, WER, akurasi kata, exact match,
serta precision/recall/F1 tingkat karakter dari alignment edit-distance.

    python scripts/metrics_report.py --model models/aksara_crnn.keras \
        --real_csv data/real/labels.csv --per-gaya

Kenapa P/R/F1 dihitung dari alignment: pengenalan baris teks bukan klasifikasi satu
label, jadi tidak ada "true positive" yang alami. Dengan menyelaraskan (alignment)
prediksi dan label, kecocokan karakter berperan sebagai TP, karakter berlebih
sebagai FP (insersi), dan karakter hilang sebagai FN (delisi). Hasilnya F1 yang
bermakna dan bisa dibandingkan dengan metrik klasifikasi di literatur.
"""
import argparse
import collections
import csv
import os
import sys

import numpy as np
import tensorflow as tf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aksara import charset  # noqa: E402
from aksara.model import greedy_decode  # noqa: E402
from aksara.preprocess import preprocess  # noqa: E402


def read_image(path):
    """cv2.imread gagal pada nama berkas non-ASCII di Windows."""
    import cv2

    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def edit_ops(ref, hyp):
    """Hitung substitusi, delesi, insersi, dan kecocokan lewat traceback alignment."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)

    i, j = n, m
    subs = dels = inss = matches = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1] and d[i][j] == d[i - 1][j - 1]:
            matches += 1
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + 1:
            subs += 1
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            dels += 1
            i -= 1
        else:
            inss += 1
            j -= 1
    return subs, dels, inss, matches


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="models/aksara_crnn.keras")
    ap.add_argument("--real_csv", default="data/real/labels.csv")
    ap.add_argument("--per-gaya", action="store_true")
    ap.add_argument("--worst", type=int, default=5)
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.real_csv, encoding="utf-8")))
    base = os.path.dirname(a.real_csv)
    imgs, refs, gayas = [], [], []
    for r in rows:
        img = read_image(os.path.join(base, r["file"]))
        if img is None:
            print("lewat (gambar tidak ada):", r["file"])
            continue
        imgs.append(preprocess(img))
        refs.append(r["label"])
        gayas.append(r.get("gaya", "-"))

    X = np.stack(imgs).astype(np.float32) / 255.0
    if X.ndim == 3:
        X = X[..., None]
    model = tf.keras.models.load_model(a.model, compile=False)
    logits = model(X, training=False).numpy()
    hyps = [t for t, _ in greedy_decode(logits)]

    def summarise(refs, hyps, title):
        chars_ref = sum(len(r) for r in refs)
        chars_hyp = sum(len(h) for h in hyps)
        S = D = I = M = 0
        exact = 0
        words_ref = words_bad = 0
        for r, h in zip(refs, hyps):
            s, d, i, m = edit_ops(r, h)
            S, D, I, M = S + s, D + d, I + i, M + m
            exact += int(r == h)
            rw, hw = r.split(), h.split()
            words_ref += len(rw)
            ws, wd, wi, _ = edit_ops(rw, hw)
            words_bad += ws + wd + wi
        precision = M / chars_hyp if chars_hyp else 0.0
        recall = M / chars_ref if chars_ref else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        cer = (S + D + I) / chars_ref if chars_ref else 0.0
        wer = words_bad / words_ref if words_ref else 0.0
        print(f"\n== {title} (n={len(refs)}) ==")
        print(f"CER            : {cer:.4f}")
        print(f"WER            : {wer:.4f}   (akurasi kata {1 - wer:.4f})")
        print(f"Exact match    : {exact}/{len(refs)} = {exact / len(refs):.4f}")
        print(f"Presisi char   : {precision:.4f}")
        print(f"Recall char    : {recall:.4f}")
        print(f"F1 char        : {f1:.4f}")
        print(f"Subs/Del/Ins   : {S}/{D}/{I} dari {chars_ref} karakter label")
        return cer, f1

    summarise(refs, hyps, os.path.basename(a.model))

    if a.per_gaya and any(g != "-" for g in gayas):
        for gaya in sorted(set(gayas)):
            idx = [i for i, g in enumerate(gayas) if g == gaya]
            summarise([refs[i] for i in idx], [hyps[i] for i in idx], f"gaya={gaya}")

    if a.worst:
        scored = []
        for r, h in zip(refs, hyps):
            s, d, i, _ = edit_ops(r, h)
            scored.append(((s + d + i) / max(1, len(r)), r, h))
        scored.sort(reverse=True)
        print(f"\n== {a.worst} terburuk ==")
        for cer, r, h in scored[: a.worst]:
            print(f"CER {cer:5.2f}  label: {r}\n           tebak: {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
