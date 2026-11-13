"""Impor satu batch gambar aksara dari ZIP: ekstrak, prediksi, dan siapkan verifikasi.

    python scripts/import_zip.py --zip "C:/Users/USER/Downloads/xxx.zip" \
        --out data/real/web/zip1 --csv data/real/web/labels_usulan.csv

Yang dihasilkan:
  <out>/                gambar asli hasil ekstrak
  <out>/masuk-model/    citra 32x192 yang benar-benar dilihat model (diperbesar)
  <out>/kontak.png      lembar kontak bernomor untuk disaring manual
  baris baru di CSV     label kosong, label_usulan = prediksi model, verified=no

Tidak ada label yang dianggap benar di sini: prediksi model hanya usulan.
"""
import argparse
import csv
import os
import sys
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aksara import charset  # noqa: E402
from aksara.model import greedy_decode  # noqa: E402
from aksara.preprocess import preprocess  # noqa: E402

IMAGE_EXT = {".png", ".jpg", ".jpeg"}


def read_image(path):
    """Baca gambar lewat buffer, supaya nama berkas non-ASCII (mis. paréntah.png)
    tetap terbaca di Windows — cv2.imread gagal pada path seperti itu."""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--model", default="models/aksara_crnn.keras")
    ap.add_argument("--sign-prefix", default="zip1")
    args = ap.parse_args()

    os.makedirs(os.path.join(args.out, "masuk-model"), exist_ok=True)
    with zipfile.ZipFile(args.zip) as z:
        members = [n for n in z.namelist()
                   if not n.endswith("/") and os.path.splitext(n)[1].lower() in IMAGE_EXT]
        for name in members:
            target = os.path.join(args.out, os.path.basename(name))
            with z.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())
    files = sorted(f for f in os.listdir(args.out)
                   if os.path.splitext(f)[1].lower() in IMAGE_EXT)
    print(f"gambar: {len(files)}")

    import tensorflow as tf

    model = tf.keras.models.load_model(args.model, compile=False)
    rows = []
    for i, name in enumerate(files):
        path = os.path.join(args.out, name)
        img = read_image(path)
        if img is None:
            print("gagal baca:", name)
            continue
        prep = preprocess(img)
        cv2.imwrite(os.path.join(args.out, "masuk-model", f"{os.path.splitext(name)[0]}.png"),
                    cv2.resize(prep, (768, 128), interpolation=cv2.INTER_NEAREST))
        x = prep.astype(np.float32)[None, ..., None] / 255.0
        text, conf = greedy_decode(model(x, training=False).numpy())[0]
        stem = os.path.splitext(name)[0]
        rows.append({
            "file": f"{os.path.basename(args.out)}/{name}",
            "latin": stem,
            "sign_id": f"{args.sign_prefix}-{i:02d}",
            "kondisi": "tidak diketahui",
            "varian_awalan": "",
            "label_usulan": text,
            "label": "",
            "verified": "no",
            "sumber": "arsip pengguna (ZIP)",
            "lisensi": "milik sendiri",
            "catatan": f"prediksi model, conf {conf:.3f}, {img.shape[1]}x{img.shape[0]} px",
        })
        print(f"{i:2d} {name[:34]:36s} conf={conf:.3f} -> {text!r}")

    exists = set()
    if os.path.exists(args.csv):
        exists = {r["file"] for r in csv.DictReader(open(args.csv, encoding="utf-8"))}
    new_rows = [r for r in rows if r["file"] not in exists]
    if new_rows:
        with open(args.csv, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(new_rows[0].keys()))
            if not exists:
                w.writeheader()
            w.writerows(new_rows)
    print(f"baris baru di CSV: {len(new_rows)} (dilewati: {len(rows) - len(new_rows)})")

    # lembar kontak
    cols, tw, th = 5, 330, 330
    sheet = Image.new("RGB", (cols * tw, ((len(files) + cols - 1) // cols) * th), "white")
    d = ImageDraw.Draw(sheet)
    for n, name in enumerate(files):
        p = os.path.join(args.out, name)
        im = Image.open(p).convert("RGB")
        im.thumbnail((tw - 10, th - 34))
        x, y = (n % cols) * tw + 5, (n // cols) * th + 22
        sheet.paste(im, (x, y))
        d.text((x, y - 16), f"{n:02d} {os.path.splitext(name)[0][:24]}", fill="black")
    out = os.path.join(args.out, "kontak.png")
    sheet.save(out)
    print("kontak:", out, sheet.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
