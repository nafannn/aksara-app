"""Diagnosa satu gambar: apa yang dilihat model dan apa yang keluar.

    python scripts/debug_one.py path/ke/foto.jpg --out data/debug

Menyimpan hasil preprocessing (citra yang benar-benar masuk model) dan mencetak
teks + confidence. Berguna untuk memisahkan tiga penyebab hasil ngaco:
fotonya belum berupa crop satu baris, preprocessing memotong tulisan, atau
modelnya memang salah membaca bentuk huruf.
"""
import argparse
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aksara import charset  # noqa: E402
from aksara.config import IMG_H, IMG_W  # noqa: E402
from aksara.model import greedy_decode  # noqa: E402
from aksara.preprocess import preprocess  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image")
    ap.add_argument("--model", default="models/aksara_crnn.keras")
    ap.add_argument("--out", default="data/debug")
    args = ap.parse_args()

    raw = cv2.imread(args.image)
    if raw is None:
        print(f"tidak bisa membaca gambar: {args.image}")
        return 1

    prepared = preprocess(raw)
    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.image))[0]
    raw_path = os.path.join(args.out, f"{base}-asli.png")
    pre_path = os.path.join(args.out, f"{base}-masuk-model.png")
    cv2.imwrite(raw_path, raw)
    # Masuk model itu grayscale 32x192; diperbesar hanya agar mata manusia bisa melihat.
    cv2.imwrite(pre_path, cv2.resize(prepared, (IMG_W * 4, IMG_H * 4), interpolation=cv2.INTER_NEAREST))

    import tensorflow as tf

    model = tf.keras.models.load_model(args.model, compile=False)
    x = prepared.astype(np.float32)[None, ..., None] / 255.0
    text, conf = greedy_decode(model(x, training=False).numpy())[0]

    print(f"gambar asli      : {raw.shape[1]}x{raw.shape[0]}")
    print(f"masuk model      : {prepared.shape[1]}x{prepared.shape[0]} (grayscale)")
    print(f"aksara terbaca   : {text!r}")
    print(f"confidence       : {conf:.3f}")
    print(f"jumlah karakter  : {len(text)}")
    print(f"hanya aksara?    : {charset.is_sundanese(text)}")
    print(f"disimpan         : {raw_path}")
    print(f"                   {pre_path}")
    print("\nBandingkan dua berkas itu: kalau tulisan di '-masuk-model.png' terpotong,")
    print("miring, atau ada lebih dari satu baris, masalahnya di crop/preprocessing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
