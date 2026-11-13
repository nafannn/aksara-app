"""Training CRNN-CTC. Contoh:
  python scripts/train.py --epochs 20
  python scripts/train.py --epochs 8 --init models/aksara_crnn.keras --real_csv data/real/train.csv --lr 3e-4   # fine-tune foto asli
"""
import argparse, csv, os, random, sys, time
import numpy as np, tensorflow as tf, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aksara import charset, config
from aksara.model import build_model, ctc_loss, greedy_decode
from aksara.preprocess import preprocess

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=20)
ap.add_argument("--batch", type=int, default=64)
ap.add_argument("--lr", type=float, default=2e-3)
ap.add_argument("--data", default="data")
ap.add_argument("--out", default="models/aksara_crnn.keras")
ap.add_argument("--init", default=None, help="model .keras untuk fine-tune")
ap.add_argument("--real_csv", default=None, help="CSV (file,label,sign_id) foto asli untuk dicampur ke training")
ap.add_argument("--real_repeat", type=int, default=5, help="oversampling data asli")
ap.add_argument("--max_len", type=int, default=36)
ap.add_argument("--limit", type=int, default=0, help="batasi jumlah sampel train (debug)")
ap.add_argument("--augment", choices=["basic", "strong"], default="basic",
                help="basic: jitter kecerahan saja; strong: tambah erosi/dilasi stroke, blur, "
                     "skala horizontal, dan noise untuk meniru tipografi plang yang dekoratif")
ap.add_argument("--time_budget_min", type=float, default=0, help="berhenti setelah N menit (0=tanpa batas)")
a = ap.parse_args()
tf.random.set_seed(config.SEED); np.random.seed(config.SEED)


def load(split):
    d = np.load(os.path.join(a.data, f"synth_{split}.npz"), allow_pickle=False)
    return d["x"], [str(s) for s in d["y"]]


def load_real(csv_path):
    base = os.path.dirname(csv_path)
    xs, ys = [], []
    for row in csv.DictReader(open(csv_path, encoding="utf-8")):
        img = cv2.imread(os.path.join(base, row["file"]))
        if img is None:
            continue
        xs.append(preprocess(img)); ys.append(row["label"])
    return np.stack(xs), ys


def pack(ys):
    enc = [charset.encode(y) for y in ys]
    L = max(len(e) for e in enc)
    lab = np.zeros((len(enc), L), np.int32)
    for i, e in enumerate(enc):
        lab[i, :len(e)] = e
    return lab, np.array([len(e) for e in enc], np.int32)


xtr, ytr = load("train"); xva, yva = load("val")
if a.real_csv:
    xr, yr = load_real(a.real_csv)
    xtr = np.concatenate([xtr] + [xr] * a.real_repeat); ytr = ytr + yr * a.real_repeat
keep = [i for i, y in enumerate(ytr) if len(charset.encode(y)) <= a.max_len]
xtr = xtr[keep]; ytr = [ytr[i] for i in keep]
if a.limit:
    xtr, ytr = xtr[:a.limit], ytr[:a.limit]
print(f"train={len(xtr)} val={len(xva)} kelas={charset.NUM_CLASSES}", flush=True)

model = tf.keras.models.load_model(a.out if False else a.init) if a.init else build_model()
print("parameter:", model.count_params(), flush=True)
steps = int(np.ceil(len(xtr) / a.batch))
sched = tf.keras.optimizers.schedules.CosineDecay(a.lr, steps * a.epochs, alpha=0.05)
opt = tf.keras.optimizers.Adam(sched)
lab_tr, len_tr = pack(ytr)


@tf.function
def train_step(x, lab, ln):
    with tf.GradientTape() as tape:
        logits = model(x, training=True)
        loss = tf.reduce_mean(ctc_loss(lab, ln, logits))
    grads = tape.gradient(loss, model.trainable_variables)
    opt.apply_gradients(zip(grads, model.trainable_variables))
    return loss


def prep(xb):
    return (xb.astype(np.float32) / 255.0)[..., None]


def _rescale_width(img, factor):
    """Ubah lebar citra (meniru huruf condensed/lebar) lalu pad ke lebar asli."""
    h, w = img.shape
    new_w = max(8, int(round(w * factor)))
    out = np.full((h, w), int(np.median(img)), dtype=np.uint8)
    resized = cv2.resize(img, (min(new_w, w), h), interpolation=cv2.INTER_AREA)
    out[:, :resized.shape[1]] = resized
    return out


def augment_strong(batch, rng):
    """Augmentasi yang menargetkan selisih tipografi: ketebalan stroke, tepi kabur,
    proporsi huruf, dan noise sensor. Diterapkan pada citra uint8 sebelum normalisasi."""
    k_dilate = np.ones((2, 2), np.uint8)
    out = []
    for img in batch:
        if rng.random() < 0.40:                      # stroke lebih tebal / lebih tipis
            img = cv2.dilate(img, k_dilate) if rng.random() < 0.5 else cv2.erode(img, k_dilate)
        if rng.random() < 0.30:                      # tepi tidak tajam (cetak plang)
            img = cv2.GaussianBlur(img, (0, 0), float(rng.uniform(0.4, 1.2)))
        if rng.random() < 0.30:                      # huruf condensed / lebar
            img = _rescale_width(img, float(rng.uniform(0.85, 1.15)))
        if rng.random() < 0.20:                      # noise
            sigma = float(rng.uniform(3, 12))
            noise = np.random.normal(0, sigma, img.shape)
            img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        out.append(img)
    return np.stack(out)


def make_batch(xtr, idx, rng, strong):
    xb = xtr[idx]
    if strong:
        xb = augment_strong(xb, rng)
    xb = prep(xb)
    xb = np.clip(xb * np.random.uniform(0.8, 1.2, (len(idx), 1, 1, 1)) +
                 np.random.uniform(-0.08, 0.08, (len(idx), 1, 1, 1)), 0, 1).astype(np.float32)
    return xb


def evaluate(x, y, bs=128):
    hyp = []
    for i in range(0, len(x), bs):
        hyp += [t for t, _ in greedy_decode(model(prep(x[i:i + bs]), training=False).numpy())]
    return charset.cer(y, hyp), charset.word_accuracy(y, hyp)


os.makedirs(os.path.dirname(a.out), exist_ok=True)
best, t0 = 9.9, time.time()
aug_rng = random.Random(config.SEED)
for ep in range(1, a.epochs + 1):
    idx = np.random.permutation(len(xtr)); losses = []
    for s in range(steps):
        b = idx[s * a.batch:(s + 1) * a.batch]
        xb = make_batch(xtr, b, aug_rng, a.augment == "strong")
        losses.append(float(train_step(xb, lab_tr[b], len_tr[b])))
    vc, vw = evaluate(xva, yva)
    print(f"epoch {ep}/{a.epochs} loss={np.mean(losses):.3f} val_CER={vc:.4f} val_wordacc={vw:.4f} "
          f"({(time.time()-t0)/60:.1f} mnt)", flush=True)
    if vc < best:
        best = vc; model.save(a.out)
    if a.time_budget_min and (time.time() - t0) / 60 > a.time_budget_min:
        print("batas waktu tercapai, berhenti.", flush=True); break
print("selesai. val_CER terbaik:", round(best, 4), "->", a.out, flush=True)
