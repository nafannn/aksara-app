"""Bagi labels.csv asli menjadi latih/uji berdasarkan GAYA penulisan.

    python scripts/make_real_splits.py --csv data/real/labels.csv --test-gaya plang

Split per gaya (bukan per gambar) mencegah kebocoran: potongan dari sumber yang sama
tidak boleh ada di latih dan uji sekaligus. Contoh pemakaian pada proyek ini:
latih = tulisan tangan + cetak + neon + ukir, uji = plang jalan.
"""
import argparse
import collections
import csv
import os


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="data/real/labels.csv")
    ap.add_argument("--test-gaya", action="append", required=True,
                    help="gaya yang dijadikan uji (boleh berulang)")
    ap.add_argument("--out-dir", default="data/real")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    if rows and "gaya" not in rows[0]:
        print("kolom 'gaya' tidak ada di CSV; tambahkan dulu")
        return 1

    train = [r for r in rows if r["gaya"] not in set(args.test_gaya)]
    test = [r for r in rows if r["gaya"] in set(args.test_gaya)]
    for name, subset in (("train", train), ("test", test)):
        path = os.path.join(args.out_dir, f"{'-'.join(args.test_gaya)}-{name}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(subset)
        print(f"{name:5s} n={len(subset):3d} {dict(collections.Counter(r['gaya'] for r in subset))} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
