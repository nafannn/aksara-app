"""Antarmuka yang dipakai B (backend Flask). Kontrak:

    recognize(image: np.ndarray BGR/gray) -> {"aksara": str, "confidence": float}

- `image` = crop baris aksara dari user (cropper di UI).
- Mode MOCK (AKSARA_MOCK=1): selalu mengembalikan kata tetap, untuk integrasi sebelum model jadi.
- Model dimuat sekali (lazy). Path bisa diganti lewat env AKSARA_MODEL.
"""
import os
import numpy as np

_MODEL = None
MODEL_PATH = os.environ.get("AKSARA_MODEL", os.path.join(os.path.dirname(__file__), "..", "models", "aksara_crnn.keras"))


def _load():
    global _MODEL
    if _MODEL is None:
        import tensorflow as tf
        _MODEL = tf.keras.models.load_model(MODEL_PATH, compile=False)
    return _MODEL


def recognize(image: np.ndarray) -> dict:
    if os.environ.get("AKSARA_MOCK") == "1":
        return {"aksara": "ᮘᮢᮌ", "confidence": 0.99}      # "braga"
    from .preprocess import preprocess
    from .model import greedy_decode
    x = preprocess(image).astype(np.float32)[None, ..., None] / 255.0
    text, conf = greedy_decode(_load()(x, training=False).numpy())[0]
    return {"aksara": text, "confidence": round(conf, 4)}
