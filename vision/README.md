# AKSARA: modul Vision & Model (Peran A)

Mengubah **foto crop satu baris Aksara Sunda** menjadi **string Unicode + confidence**.
Transliterasi ke Latin, arti, dan audio dikerjakan B/C; modul ini hanya sampai teks Aksara.

## Status jujur (baca dulu)
| Hal | Status |
|---|---|
| Pipeline lengkap (data sintetis → preprocessing → CRNN-CTC → `recognize()` → evaluasi) | ✅ jalan end-to-end |
| Model terlatih `models/aksara_crnn.keras` | ✅ dilatih 20 epoch di CPU |
| Hasil pada **test set sintetis** (800 gambar) | CER **5,4%**, akurasi kata **76,8%** |
| Hasil pada **foto plang asli** | ❌ **belum diuji** (belum ada foto berlabel). Angka di atas optimistis karena test set dibuat dengan generator yang sama |
| Font | hanya Noto Sans Sundanese. Plang asli memakai tipografi dekoratif → akan ada selisih performa (domain gap) |
| `latin2aksara.py` | aturan dasar untuk membuat label; **bukan** transliterator produksi, perlu verifikasi manual |

Kesalahan terbanyak model: `paneuleung ↔ pamepet` (eu vs e, bentuknya mirip), `panyecek ↔ panghulu`, dan `xa → sa`.

## Isi folder
```
aksara/charset.py        66 kelas token (blank, spasi, codepoint U+1B80–1BBF) + fungsi CER
aksara/latin2aksara.py   Latin → Aksara (untuk label/data)
aksara/synth.py          generator "foto plang" tiruan (A1)
aksara/preprocess.py     preprocessing OpenCV (A2)
aksara/model.py          CRNN + CTC (A3)
aksara/recognize.py      antarmuka untuk B: recognize(image) → {aksara, confidence}  (A4)
scripts/make_dataset.py  buat dataset sintetis
scripts/train.py         training / fine-tune
scripts/evaluate.py      evaluasi teknis (A5)
scripts/split_real.py    split foto asli PER PLANG
fonts/  data/  models/
```

## Cara menjalankan (urut)
```bash
pip install -r requirements.txt
python scripts/make_dataset.py --preview        # cek data/preview.png: kiri foto tiruan, kanan hasil preprocessing
python scripts/train.py --epochs 20             # ~25 menit di CPU; di Colab GPU jauh lebih cepat
python scripts/evaluate.py --synth test
```
Di Colab/Kaggle GPU: ubah `IMG_H=64, IMG_W=320` di `aksara/config.py` (rarangkén lebih jelas), lalu ulangi tiga langkah di atas.

## Roadmap A (urutan terbaik)
| Langkah | Apa | Selesai jika | Status |
|---|---|---|---|
| 1 | Pipeline sintetis + model baseline | `recognize()` jalan | ✅ selesai |
| 2 | **Kirim `recognize()` ke B** (lihat kontrak di bawah) | B bisa memanggil dari Flask | siap dikirim |
| 3 | **Kumpulkan foto plang asli** (target awal ±100 foto, ≥30 plang berbeda) | file `data/real/labels.csv` terisi | ⏳ butuh kamu + tim |
| 4 | Fine-tune dengan foto asli (split train) | CER test asli turun | setelah langkah 3 |
| 5 | Tambah font dekoratif + augmentasi sesuai kegagalan di foto asli | CER per kondisi membaik | iteratif |
| 6 | Evaluasi final + tulis Bab V (CER, akurasi kata, confusion, per kondisi) | tabel hasil | akhir |

### Langkah 3–4 dengan foto asli
1. Foto tiap plang dari beberapa kondisi (siang/malam/miring). **Crop manual hanya baris Aksara.**
2. Isi `data/real/labels.csv` (lihat `labels_contoh.csv`): kolom `file,label,sign_id,kondisi`. `label` = string Aksara Unicode (boleh dibantu `latin_to_aksara`, lalu cek manual). Foto dari plang yang sama harus punya `sign_id` yang sama.
3. `python scripts/split_real.py data/real/labels.csv` → membuat train/val/test **per plang**.
4. `python scripts/train.py --epochs 8 --lr 3e-4 --init models/aksara_crnn.keras --real_csv data/real/train.csv`
5. `python scripts/evaluate.py --real_csv data/real/test.csv` → inilah angka yang boleh masuk laporan.

**Aturan yang tidak boleh dilanggar:** test set dipisah sejak awal dan tidak dipakai untuk tuning; foto dari plang yang sama tidak boleh ada di train dan test sekaligus.

## Kontrak untuk B
```python
from aksara.recognize import recognize
hasil = recognize(image)        # image: np.ndarray (BGR/gray) crop baris aksara
# → {"aksara": "ᮘᮢᮌ", "confidence": 0.91}
```
- Set env `AKSARA_MOCK=1` untuk jawaban tetap ("ᮘᮢᮌ") sebelum model terpasang.
- Path model: `models/aksara_crnn.keras` (atau env `AKSARA_MODEL`).
- `confidence` = rata-rata geometrik probabilitas frame non-blank; pada tes sintetis, benar ≈ 0,97 vs salah ≈ 0,88. Tentukan ambang tolak bersama C setelah ada data asli.
- Input harus berupa crop baris aksara. Foto utuh plang belum didukung (detection otomatis = stretch goal).

## Catatan untuk laporan
- Bab IV: alur gambar → grayscale → normalisasi polaritas → perkecil → crop → deskew (projection profile) → CLAHE + denoise → resize 32×192 → CRNN (CNN 4 blok, BiLSTM 96, CTC) → greedy decoding.
- Binarisasi sengaja tidak dijadikan keluaran preprocessing (bisa membuang rarangkén tipis); hanya dipakai internal untuk mencari posisi teks. Ini bisa dijadikan eksperimen pembanding di Bab V.
- Jangan melaporkan CER sintetis sebagai akurasi sistem; laporkan sebagai uji sanity terpisah.
