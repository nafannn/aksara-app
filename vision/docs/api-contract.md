# Kontrak API AKSARA

Status: **DRAFT** (menunggu review B dan C). Perubahan harus diberitahukan ke semua anggota.
Pemilik keputusan akhir: B. Reviewer: A dan C.

## Endpoint

### `POST /api/recognize`
Mengenali satu baris aksara dari gambar, lalu mengembalikan transliterasi, arti, dan audio.

**Request**
- `Content-Type: multipart/form-data`
- Field `image`: berkas gambar (JPEG atau PNG)
- Gambar harus berupa **crop baris aksara** (dibuat oleh cropper di UI). Foto utuh plang belum didukung.
- Batas ukuran berkas dan resize di klien: *diputuskan di T0.2* (usulan: resize sisi terpanjang sebelum upload).

**Response 200**
```json
{
  "status": "ok",
  "aksara": "ᮘᮢᮌ",
  "latin": "braga",
  "confidence": 0.91,
  "chars": [
    {"glyph": "ᮘᮢ", "latin": "bra", "note": "ngalagena + panyakra"},
    {"glyph": "ᮌ",  "latin": "ga",  "note": "ngalagena"}
  ],
  "meaning": "…",
  "audio_url": "/audio/braga.mp3"
}
```

| Field | Tipe | Sumber | Keterangan |
|---|---|---|---|
| `status` | string | B | `ok`, `unrecognized`, `not_found` (lihat di bawah) |
| `aksara` | string | **A** | Hasil pengenalan, string Unicode (U+1B80–U+1BBF dan spasi). UTF-8 |
| `confidence` | number 0–1 | **A** | Rata-rata geometrik probabilitas frame non-blank (satu nilai per baris) |
| `latin` | string | B | Hasil transliterasi dari `aksara` |
| `chars` | array | B | Pemecahan per karakter untuk tampilan belajar (bentuk, bunyi). Isi field `note` ditentukan B dan C |
| `meaning` | string atau null | B | Arti dari leksikon SQLite; `null` jika tidak ada |
| `audio_url` | string atau null | B | Path relatif ke berkas audio; `null` jika tidak ada |

**Nilai `status`**

| Nilai | Arti | Isi response |
|---|---|---|
| `ok` | Dikenali, ditemukan di leksikon | Semua field terisi |
| `not_found` | Dikenali dan ditransliterasi, tetapi kata tidak ada di leksikon | `aksara`, `latin`, `chars` tetap diisi; `meaning` dan `audio_url` = `null` |
| `unrecognized` | Model tidak menghasilkan teks (atau gambar tidak dapat diproses) | `aksara` = `""`; field lain kosong atau `null` |

**Error**

| HTTP | Kondisi | Body |
|---|---|---|
| 400 | Field `image` tidak ada atau berkas bukan gambar yang valid | `{"status": "error", "message": "..."}` |
| 413 | Berkas terlalu besar | idem |
| 415 | Tipe berkas tidak didukung | idem |
| 500 | Kesalahan server | idem |

### `GET /audio/<nama_berkas>`
Mengembalikan berkas audio untuk `audio_url`. Format: *diputuskan di T0.2* (usulan: MP3, kompatibel lintas browser).

## Cara B memanggil modul A

```python
import cv2, numpy as np
from aksara.recognize import recognize   # PYTHONPATH harus menunjuk ke vision/

data = request.files["image"].read()
img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
if img is None:
    ...  # 400
hasil = recognize(img)          # {"aksara": str, "confidence": float}
```
- Mode mock: set env `AKSARA_MOCK=1` → selalu mengembalikan `{"aksara": "ᮘᮢᮌ", "confidence": 0.99}`.
- Lokasi model: `vision/models/aksara_crnn.keras` (atau env `AKSARA_MODEL`).
- Model dimuat sekali (lazy) pada pemanggilan pertama; panggilan pertama lebih lambat.

## Catatan penting
- **Confidence belum dapat dijadikan ambang tolak.** Pada tes sintetis nilainya membedakan benar dan salah dengan baik (≈0,97 vs ≈0,88), tetapi pada satu foto asli, hasil dengan satu karakter salah tetap mendapat 0,95. Ambang ditentukan setelah ada data asli.
- `confidence` saat ini satu nilai per baris, bukan per karakter.
- Semua teks dikirim sebagai UTF-8; pastikan JSON tidak meng-escape karakter Sunda secara tidak konsisten antara backend dan frontend.

## Pertanyaan terbuka (putuskan di T0.2)
1. Apakah perlu status `low_confidence` terpisah dari `ok`? (Bergantung pada ambang dari data asli.)
2. Isi dan format field `note` pada `chars`.
3. Batas ukuran upload, ukuran resize klien, dan format audio.
4. Apakah satu request boleh berisi beberapa baris (saat ini satu baris per request).
