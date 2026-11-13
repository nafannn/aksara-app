"""Bandingkan beberapa model pada test sintetis dan/atau crop foto asli.

    python scripts/compare_models.py \
        --model models/aksara_crnn.keras --model models/exp_strong.keras \
        --real_csv data/real/labels.csv --synth test

Keluaran: satu baris ringkas per model (CER, akurasi kata) untuk tiap dataset,
supaya pengaruh perubahan training bisa dibaca tanpa menebak.
"""
import argparse
import csv
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aksara import charset  # noqa: E402
from aksara.model import greedy_decode  # noqa: E402
from aksara.preprocess import preprocess  # noqa: E402


def read_image(path):
    """cv2.imread gagal pada nama berkas non-ASCII di Windows."""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def load_real(csv_path):
    base = os.path.dirname(csv_path)
    xs, ys = [], []
    for row in csv.DictReader(open(csv_path, encoding="utf-8")):
        img = read_image(os.path.join(base, row["file"]))
        if img is None:
            print("lewat (gambar tidak ada):", row["file"])
            continue
        xs.append(preprocess(img))
        ys.append(row["label"])
    return (np.stack(xs) if xs else np.zeros((0, 32, 192), np.uint8)), ys


def predict(model, X, batch=64):
    texts, confs = [], []
    for i in range(0, len(X), batch):
        chunk = (X[i:i + batch].astype(np.float32) / 255.0)[..., None]
        out = greedy_decode(model(chunk, training=False).numpy())
        texts += [t for t, _ in out]
        confs += [c for _, c in out]
    return texts, confs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", action="append", required=True)
    ap.add_argument("--synth", default=None, help="split sintetis: val atau test")
    ap.add_argument("--data", default="data")
    ap.add_argument("--real_csv", default=None)
    args = ap.parse_args()

    import tensorflow as tf

    datasets = []
    if args.synth:
        d = np.load(os.path.join(args.data, f"synth_{args.synth}.npz"))
        datasets.append((f"sintetis-{args.synth}", d["x"], [str(s) for s in d["y"]]))
    if args.real_csv:
        xr, yr = load_real(args.real_csv)
        if len(xr):
            datasets.append(("foto-asli", xr, yr))

    if not datasets:
        print("tidak ada dataset; pakai --synth atau --real_csv")
        return 1

    print(f"{'model':28s} {'dataset':16s} {'n':>4s} {'CER':>7s} {'kata':>7s}")
    for path in args.model:
        model = tf.keras.models.load_model(path, compile=False)
        for name, X, Y in datasets:
            hyp, _ = predict(model, X)
            cer = charset.cer(Y, hyp)
            acc = charset.word_accuracy(Y, hyp)
            print(f"{os.path.basename(path):28s} {name:16s} {len(Y):4d} {cer:7.4f} {acc:7.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
