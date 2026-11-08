"""Buat dataset sintetis -> data/synth_{split}.npz  (x: N,H,W uint8; y: string Unicode)."""
import argparse, os, random, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aksara import synth, config
from aksara.preprocess import preprocess

ap = argparse.ArgumentParser()
ap.add_argument("--n_train", type=int, default=12000)
ap.add_argument("--n_val", type=int, default=1200)
ap.add_argument("--n_test", type=int, default=1200)
ap.add_argument("--font_dir", default=config.FONT_DIR)
ap.add_argument("--out", default="data")
ap.add_argument("--preview", action="store_true")
a = ap.parse_args()

fonts = synth.find_fonts(a.font_dir)
seeds = synth.load_seed_words(os.path.join(a.out, "words_seed.txt"))
os.makedirs(a.out, exist_ok=True)
for split, n, seed in [("train", a.n_train, 1), ("val", a.n_val, 2), ("test", a.n_test, 3)]:
    rng = random.Random(config.SEED * 100 + seed)
    xs, ys, raws = [], [], []
    for i in range(n):
        t = synth.random_text(rng, seeds)
        raw = synth.render_photo(t, fonts, rng)
        xs.append(preprocess(raw)); ys.append(t)
        if a.preview and i < 24:
            raws.append(raw)
    np.savez_compressed(os.path.join(a.out, f"synth_{split}.npz"), x=np.stack(xs), y=np.array(ys))
    print(split, len(xs))
    if a.preview and split == "train":
        rows = []
        for raw, x in zip(raws, xs[:24]):
            r = cv2.resize(raw, (480, 80)); p = cv2.cvtColor(cv2.resize(x, (480, 80)), cv2.COLOR_GRAY2BGR)
            rows.append(np.hstack([r, p]))
        cv2.imwrite(os.path.join(a.out, "preview.png"), np.vstack(rows[:12]))
