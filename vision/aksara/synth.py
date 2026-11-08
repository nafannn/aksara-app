"""Generator data sintetis (A1): teks Aksara Sunda -> 'foto plang' tiruan.

Meniru kondisi dunia nyata: warna latar/teks beragam (termasuk teks terang di latar gelap),
perspektif, rotasi, blur, noise, glare, bayangan, kompresi JPEG, resolusi rendah.
"""
import glob
import os
import random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .charset import SWARA, NGALAGENA, NGALAGENA_TAMBAHAN, SIGN_AKHIR, MEDIAL, VOKAL, PAMAEH
from .latin2aksara import latin_to_aksara


# ---------- teks ----------
def random_syllable(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.08:
        return rng.choice(SWARA)
    pool = NGALAGENA if rng.random() < 0.92 else NGALAGENA_TAMBAHAN
    s = rng.choice(pool)
    if rng.random() < 0.18:
        s += rng.choice(MEDIAL)
    if rng.random() < 0.55:
        s += rng.choice(VOKAL)
    q = rng.random()
    if q < 0.22:
        s += rng.choice(SIGN_AKHIR)
    elif q < 0.30 and not s.endswith(tuple(VOKAL)):
        s += PAMAEH
    return s


def random_word(rng: random.Random) -> str:
    return "".join(random_syllable(rng) for _ in range(rng.randint(1, 4)))


def load_seed_words(path: str):
    with open(path, encoding="utf-8") as f:
        return [latin_to_aksara(l.strip()) for l in f if l.strip()]


def random_text(rng: random.Random, seed_words) -> str:
    if seed_words and rng.random() < 0.5:
        parts = [rng.choice(seed_words) for _ in range(rng.choice([1, 1, 2]))]
    else:
        parts = [random_word(rng) for _ in range(rng.choice([1, 1, 2]))]
    return " ".join(parts)


# ---------- render ----------
def _lum(bgr):
    b, g, r = bgr
    return 0.114 * b + 0.587 * g + 0.299 * r


def _pick_colors(rng):
    bg = [rng.randint(0, 255) for _ in range(3)]
    if rng.random() < 0.5:   # warna plang umum: hijau, biru, merah marun, putih, hitam
        bg = rng.choice([[40, 90, 40], [120, 70, 20], [40, 30, 110], [240, 240, 240],
                         [30, 30, 30], [90, 120, 60], [50, 50, 130], [200, 220, 230]])
        bg = [int(np.clip(c + rng.randint(-25, 25), 0, 255)) for c in bg]
    fg = [255, 255, 255] if _lum(bg) < 135 else [15, 15, 15]
    fg = [int(np.clip(c + rng.randint(-35, 35), 0, 255)) for c in fg]
    if abs(_lum(fg) - _lum(bg)) < 70:
        fg = [255, 255, 255] if _lum(bg) < 135 else [0, 0, 0]
    return bg, fg


def _render_mask(text, font_path, size, stroke, rng):
    font = ImageFont.truetype(font_path, size, layout_engine=ImageFont.Layout.RAQM)
    probe = Image.new("L", (size * (len(text) + 4), size * 3), 0)
    d = ImageDraw.Draw(probe)
    d.text((size, size), text, font=font, fill=255, stroke_width=stroke)
    arr = np.array(probe)
    pts = cv2.findNonZero(arr)
    x, y, w, h = cv2.boundingRect(pts)
    return arr[y:y + h, x:x + w]


def _gradient(h, w, rng, strength):
    ang = rng.uniform(0, np.pi)
    xs, ys = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
    g = xs * np.cos(ang) + ys * np.sin(ang)
    return (g * strength).astype(np.float32)


def _perspective(img, rng, max_frac):
    h, w = img.shape[:2]
    j = lambda m: rng.uniform(-max_frac, max_frac) * m
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[j(w), j(h)], [w + j(w), j(h)], [w + j(w), h + j(h)], [j(w), h + j(h)]])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def render_photo(text, font_paths, rng: random.Random) -> np.ndarray:
    font_path = rng.choice(font_paths)
    size = rng.randint(44, 90)
    stroke = rng.choice([0, 0, 1, 2])
    mask = _render_mask(text, font_path, size, stroke, rng)
    mh, mw = mask.shape
    padx, pady = int(mw * rng.uniform(0.06, 0.4)), int(mh * rng.uniform(0.15, 0.7))
    H, W = mh + 2 * pady, mw + 2 * padx
    bg, fg = _pick_colors(rng)
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[:] = bg
    canvas += _gradient(H, W, rng, rng.uniform(0, 35))[..., None]
    m = np.zeros((H, W), np.float32)
    m[pady:pady + mh, padx:padx + mw] = mask / 255.0
    if rng.random() < 0.35:   # variasi ketebalan
        k = np.ones((2, 2), np.uint8)
        m = cv2.dilate(m, k) if rng.random() < 0.5 else cv2.erode(m, k)
    for c in range(3):
        canvas[..., c] = canvas[..., c] * (1 - m) + fg[c] * m
    if rng.random() < 0.3:    # garis/bingkai plang
        t = rng.randint(1, 3)
        cv2.rectangle(canvas, (t, t), (W - t - 1, H - t - 1), fg, t)
    img = np.clip(canvas, 0, 255).astype(np.uint8)

    # geometri
    img = _perspective(img, rng, rng.uniform(0.0, 0.07))
    ang = rng.gauss(0, 3.0)
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, 1.0)
    img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

    # efek foto
    f = img.astype(np.float32)
    if rng.random() < 0.2:    # glare
        cx, cy = rng.randint(0, W), rng.randint(0, H)
        yy, xx = np.mgrid[0:H, 0:W]
        glow = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (0.35 * W) ** 2)))
        f += glow[..., None] * rng.uniform(40, 110)
    if rng.random() < 0.25:   # bayangan
        f *= (1 - 0.35 * np.clip(_gradient(H, W, rng, 1.0), 0, 1))[..., None]
    f = f * rng.uniform(0.65, 1.25) + rng.uniform(-30, 30)
    img = np.clip(f, 0, 255).astype(np.uint8)

    if rng.random() < 0.5:    # resolusi rendah
        s = rng.uniform(0.25, 0.7)
        img = cv2.resize(img, (max(8, int(W * s)), max(8, int(H * s))), interpolation=cv2.INTER_AREA)
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
    sigma = rng.choice([0, 0, 0.5, 0.9, 1.4, 1.9])
    if sigma:
        img = cv2.GaussianBlur(img, (0, 0), sigma)
    if rng.random() < 0.2:    # motion blur
        k = rng.choice([3, 5, 7])
        kern = np.zeros((k, k), np.float32)
        kern[k // 2, :] = 1.0 / k
        img = cv2.filter2D(img, -1, kern)
    noise = rng.choice([0, 3, 6, 10, 14])
    if noise:
        n = np.random.default_rng(rng.randint(0, 2**31)).normal(0, noise, img.shape)
        img = np.clip(img.astype(np.float32) + n, 0, 255).astype(np.uint8)
    q = rng.randint(30, 92)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def find_fonts(font_dir: str):
    paths = sorted(glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(os.path.join(font_dir, "*.otf")))
    if not paths:
        raise FileNotFoundError(f"Tidak ada font .ttf/.otf di {font_dir}")
    return paths
