"""Evaluasi teknis (A5). Dua mode:
  python scripts/evaluate.py --synth test                       # test set sintetis
  python scripts/evaluate.py --real_csv data/real/test.csv      # foto asli (file,label,sign_id[,kondisi])
Keluaran: CER, akurasi kata, rata-rata confidence benar vs salah, kesalahan karakter terbanyak,
dan (jika ada kolom 'kondisi') CER per kondisi.
"""
import argparse, csv, os, sys, collections, json
import numpy as np, tensorflow as tf, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aksara import charset
from aksara.model import greedy_decode
from aksara.preprocess import preprocess


def read_image(path):
    """cv2.imread gagal pada nama berkas non-ASCII di Windows (mis. paréntah.png)."""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="models/aksara_crnn.keras")
ap.add_argument("--synth", default=None)
ap.add_argument("--real_csv", default=None)
ap.add_argument("--data", default="data")
ap.add_argument("--json_out", default=None)
a = ap.parse_args()

model = tf.keras.models.load_model(a.model, compile=False)
if a.synth:
    d = np.load(os.path.join(a.data, f"synth_{a.synth}.npz")); X, Y = d["x"], [str(s) for s in d["y"]]; K = [""] * len(Y)
else:
    base = os.path.dirname(a.real_csv); X, Y, K = [], [], []
    for r in csv.DictReader(open(a.real_csv, encoding="utf-8")):
        im = read_image(os.path.join(base, r["file"]))
        if im is not None:
            X.append(preprocess(im)); Y.append(r["label"]); K.append(r.get("kondisi", ""))
    X = np.stack(X)

hyp, conf = [], []
for i in range(0, len(X), 128):
    out = greedy_decode(model((X[i:i + 128].astype(np.float32) / 255.0)[..., None], training=False).numpy())
    hyp += [t for t, _ in out]; conf += [c for _, c in out]

ok = [h == y for h, y in zip(hyp, Y)]
res = {"n": len(Y), "CER": round(charset.cer(Y, hyp), 4), "word_acc": round(float(np.mean(ok)), 4),
       "conf_benar": round(float(np.mean([c for c, o in zip(conf, ok) if o])) if any(ok) else 0, 4),
       "conf_salah": round(float(np.mean([c for c, o in zip(conf, ok) if not o])) if not all(ok) else 0, 4)}
print(json.dumps(res, indent=2))

# kesalahan karakter terbanyak (sederhana: pasangan ref/hyp pada posisi yang sama jika panjang sama)
sub = collections.Counter()
for y, h in zip(Y, hyp):
    if len(y) == len(h):
        for cy, ch in zip(y, h):
            if cy != ch:
                sub[(cy, ch)] += 1
print("substitusi terbanyak (ref -> hyp):", [(f"U+{ord(k[0]):04X}->U+{ord(k[1]):04X}", v) for k, v in sub.most_common(8)])

if any(K):
    for k in sorted(set(K)):
        idx = [i for i, kk in enumerate(K) if kk == k]
        print(f"kondisi={k:15s} n={len(idx):3d} CER={charset.cer([Y[i] for i in idx], [hyp[i] for i in idx]):.4f}")
if a.json_out:
    json.dump(res, open(a.json_out, "w"), indent=2)
