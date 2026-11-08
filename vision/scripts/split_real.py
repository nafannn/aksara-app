"""Pisahkan foto asli per PLANG (bukan per foto) agar tidak terjadi kebocoran data.
Masukan : data/real/labels.csv  dengan kolom  file,label,sign_id[,kondisi]
Keluaran: data/real/{train,val,test}.csv  (sign_id yang sama selalu masuk split yang sama)
"""
import csv, os, random, sys
path = sys.argv[1] if len(sys.argv) > 1 else "data/real/labels.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))
signs = sorted({r["sign_id"] for r in rows}); random.Random(7).shuffle(signs)
n = len(signs); cut1, cut2 = int(n * 0.6), int(n * 0.8)
where = {s: ("train" if i < cut1 else "val" if i < cut2 else "test") for i, s in enumerate(signs)}
for split in ("train", "val", "test"):
    sub = [r for r in rows if where[r["sign_id"]] == split]
    with open(os.path.join(os.path.dirname(path), f"{split}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(sub)
    print(split, len(sub), "foto,", len({r['sign_id'] for r in sub}), "plang")
