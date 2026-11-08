"""Preprocessing OpenCV (A2): foto crop baris aksara -> citra model (IMG_H x IMG_W, uint8).

Urutan: grayscale -> normalisasi polaritas (teks gelap di latar terang) -> CLAHE
-> denoise ringan -> deskew (projection profile) -> crop rapat -> resize + padding.
Binarisasi sengaja TIDAK dipakai sebagai keluaran: binarisasi agresif bisa membuang
rarangkén yang tipis. Biner hanya dipakai internal untuk mencari posisi teks.
"""
import cv2
import numpy as np
from .config import IMG_H, IMG_W


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def _otsu_text_mask(gray: np.ndarray) -> np.ndarray:
    """Mask teks (255 = teks); asumsi teks gelap di latar terang.
    Gabungan Otsu (global) + adaptif (tahan gradien/bayangan) supaya bagian teks
    yang kontrasnya rendah tidak terpotong saat crop."""
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ad = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 21, 10)
    ad = cv2.medianBlur(ad, 3)
    # Otsu pada latar bergradien bisa menandai separuh gambar sebagai 'teks' -> pakai adaptif saja
    mask = ad if (bw == 255).mean() > 0.4 else cv2.bitwise_or(bw, ad)
    return mask


def normalize_polarity(gray: np.ndarray) -> np.ndarray:
    """Pastikan teks gelap di latar terang.
    Latar diperkirakan dari median piksel tepi (teks adalah minoritas piksel)."""
    h, w = gray.shape
    b = max(1, int(min(h, w) * 0.12))
    border = np.concatenate([gray[:b].ravel(), gray[-b:].ravel(),
                             gray[:, :b].ravel(), gray[:, -b:].ravel()])
    return 255 - gray if np.median(border) < 128 else gray


def enhance(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    out = clahe.apply(gray)
    return cv2.fastNlMeansDenoising(out, None, h=7, templateWindowSize=5, searchWindowSize=15)


def estimate_skew(gray: np.ndarray, max_angle: float = 10.0, step: float = 0.5) -> float:
    mask = _otsu_text_mask(gray)
    h, w = mask.shape
    best, best_score = 0.0, -1.0
    for a in np.arange(-max_angle, max_angle + 1e-6, step):
        M = cv2.getRotationMatrix2D((w / 2, h / 2), a, 1.0)
        r = cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_NEAREST)
        score = np.var(r.sum(axis=1).astype(np.float32))
        if score > best_score:
            best, best_score = a, score
    return best


def deskew(gray: np.ndarray) -> np.ndarray:
    a = estimate_skew(gray)
    if abs(a) < 0.5:
        return gray
    h, w = gray.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), a, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def crop_to_text(gray: np.ndarray, margin: float = 0.12) -> np.ndarray:
    mask = _otsu_text_mask(gray)
    pts = cv2.findNonZero(mask)
    if pts is None or len(pts) < 20:
        return gray
    x, y, w, h = cv2.boundingRect(pts)
    mx, my = int(w * margin) + 2, int(h * margin) + 2
    H, W = gray.shape
    return gray[max(y - my, 0):min(y + h + my, H), max(x - mx, 0):min(x + w + mx, W)]


def fit_to_canvas(gray: np.ndarray, h: int = IMG_H, w: int = IMG_W) -> np.ndarray:
    gh, gw = gray.shape
    new_w = max(1, int(round(gw * h / gh)))
    resized = cv2.resize(gray, (min(new_w, w), h), interpolation=cv2.INTER_AREA)
    canvas = np.full((h, w), int(np.median(gray)), dtype=np.uint8)
    canvas[:, :resized.shape[1]] = resized
    return canvas


def limit_size(gray: np.ndarray, max_h: int = 96) -> np.ndarray:
    """Perkecil foto resolusi tinggi dulu (hemat waktu; model toh hanya melihat IMG_H piksel)."""
    h, w = gray.shape
    if h <= max_h:
        return gray
    s = max_h / h
    return cv2.resize(gray, (max(1, int(w * s)), max_h), interpolation=cv2.INTER_AREA)


def preprocess(img: np.ndarray) -> np.ndarray:
    """Foto crop (BGR/gray, uint8) -> (IMG_H, IMG_W) uint8, teks gelap di latar terang."""
    g = to_gray(img)
    g = normalize_polarity(g)
    g = limit_size(g)
    g = crop_to_text(g)
    g = deskew(g)
    g = crop_to_text(g)
    g = enhance(g)
    return fit_to_canvas(g)
