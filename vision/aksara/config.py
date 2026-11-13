"""Konfigurasi bersama. Ukuran kecil supaya bisa dilatih di CPU; naikkan lewat env
untuk eksperimen resolusi tanpa mengubah default yang dipakai backend:

    AKSARA_IMG_H=64 AKSARA_IMG_W=320 python scripts/train.py --out models/exp_64x320.keras

Model hasil eksperimen harus dipakai bersama env yang sama, karena bentuk input
tertanam di dalam model.
"""
import os

IMG_H = int(os.environ.get("AKSARA_IMG_H", "32"))
IMG_W = int(os.environ.get("AKSARA_IMG_W", "192"))
SEED = 42
FONT_DIR = "fonts"
