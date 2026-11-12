# Kontrak API AKSARA

Versi: **0.2 (DRAFT)**
**Keputusan: skema respons mengikuti frontend** (`frontend/src/services/result.js`). Backend menyesuaikan, frontend tidak diubah.
Pemilik keputusan akhir: B. Reviewer: A dan C. Perubahan harus diumumkan ke semua anggota.

## Endpoint

### `POST /api/recognize`
Mengenali satu baris aksara dari gambar, lalu mengembalikan transliterasi, arti, penjelasan karakter, dan audio.

**Request**
- `Content-Type: multipart/form-data`
- Field `image`: berkas gambar (JPEG atau PNG). Frontend mengirim hasil crop dari cropper di UI.
- Gambar harus berupa **crop baris aksara**. Foto utuh plang belum didukung.

**Response 200**
```json
{
  "success": true,
  "aksara": "ᮘᮔ᮪ᮓᮥᮀ",
  "latin": "Bandung",
  "meaning": "Nama kota di Jawa Barat",
  "audio_url": "/audio/bandung.mp3",
  "character_details": [
    {"aksara": "ᮘ",  "reading": "ba", "category": "Aksara dasar",
     "explanation": "Bagian awal kata Bandung dibaca “ba”."},
    {"aksara": "ᮔ᮪", "reading": "n",  "category": "Aksara dengan pamaéh",
     "explanation": "Pamaéh menghilangkan vokal bawaan pada aksara na."},
    {"aksara": "ᮓᮥ", "reading": "du", "category": "Aksara dengan panyuku",
     "explanation": "Panyuku mengubah vokal pada aksara da menjadi u."},
    {"aksara": "ᮀ",  "reading": "ng", "category": "Rarangkén panyecek",
     "explanation": "Panyecek menandai bunyi akhir “ng”."}
  ],
  "confidence": 0.99
}
```

| Field | Tipe | Sumber | Keterangan |
|---|---|---|---|
| `success` | boolean | B | `true` jika aksara berhasil dikenali; `false` jika tidak |
| `aksara` | string | **A** | Hasil pengenalan. Hanya berisi karakter U+1B80–U+1BBF dan spasi. UTF-8 |
| `latin` | string atau null | B | Hasil transliterasi. Kapitalisasi bebas; UI menampilkan apa adanya |
| `meaning` | string atau null | B | Arti dari leksikon; `null` jika kata tidak ada di leksikon |
| `audio_url` | string atau null | B | Path relatif atau URL http(s) ke audio; `null` jika tidak ada |
| `character_details` | array | B | Pemecahan per **gugus aksara** (aksara dasar + rarangkén yang menempel), urut kiri ke kanan |
| `confidence` | number 0–1, *opsional* | **A** | Satu nilai per baris. **Tidak dibaca frontend saat ini**; boleh dikirim untuk dipakai nanti |

Isi tiap elemen `character_details`: `aksara` (gugus, mis. `ᮓᮥ`), `reading` (cara baca, mis. `du`), `category` (jenis, mis. "Rarangkén panyecek"), `explanation` (penjelasan singkat untuk pembelajar).

**Kasus yang perlu ditangani backend**

| Kasus | Respons |
|---|---|
| Dikenali, ada di leksikon | `success: true`, semua field terisi |
| Dikenali, **tidak ada di leksikon** | `success: true`, `aksara`, `latin`, `character_details` terisi; `meaning` dan `audio_url` = `null`. UI menampilkan "Makna belum tersedia dalam kamus." |
| **Tidak dikenali** (model tidak menghasilkan teks, atau gambar tak bisa diproses) | **HTTP 200**, `success: false`, `aksara: ""`, field lain `null` atau `[]`. UI menampilkan "Aksara belum berhasil dikenali. Coba foto yang lebih jelas." |

Tidak ada field `status`: perbedaan kasus cukup dibaca dari `success` dan `meaning`.

**Error (HTTP non-200)**

| HTTP | Kondisi |
|---|---|
| 400 | Field `image` tidak ada atau berkas bukan gambar valid |
| 413 | Berkas terlalu besar |
| 415 | Tipe berkas tidak didukung |
| 500 | Kesalahan server |

Body: `{"success": false, "message": "..."}`. Frontend menampilkan pesan generik untuk semua respons non-2xx dan tidak membaca `message`.

### `GET /audio/<nama_berkas>`
Mengembalikan berkas audio untuk `audio_url`. Format: *diputuskan bersama* (usulan: MP3).
Frontend meresolusi `audio_url` relatif terhadap URL respons API, sehingga path relatif seperti `/audio/bandung.mp3` mengarah ke server backend.

## Catatan untuk B (backend)

```python
import cv2, numpy as np
from aksara.recognize import recognize   # PYTHONPATH harus menunjuk ke vision/

data = request.files["image"].read()
img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
if img is None:
    ...  # 400
hasil = recognize(img)          # {"aksara": str, "confidence": float}
```
- Mode mock: env `AKSARA_MOCK=1` → selalu `{"aksara": "ᮘᮢᮌ", "confidence": 0.99}`.
- Model: `vision/models/aksara_crnn.keras` (atau env `AKSARA_MODEL`). Dimuat saat pemanggilan pertama, jadi permintaan pertama lebih lambat.
- **CORS:** saat pengembangan, frontend (Vite, `localhost:5173`) memanggil backend di origin lain. Aktifkan CORS di Flask (mis. `flask-cors`) atau pakai proxy Vite.
- **Riwayat di frontend** hanya menyimpan hasil jika `success === true`, `aksara` hanya berisi karakter U+1B80–U+1BBF dan spasi, dan `latin` tidak kosong. Hasil dengan `meaning: null` tetap tersimpan selama `latin` terisi.

## Catatan untuk C (frontend)
- Tidak ada perubahan wajib. `normalizeResult()` sudah membaca semua field di atas dan mengabaikan field yang tidak dikenal (`confidence`).
- Halaman hasil sudah menangani `latin`, `meaning`, dan `audio_url` bernilai `null`.

## Catatan penting
- **Confidence belum bisa dijadikan ambang tolak.** Pada tes sintetis, hasil benar ≈ 0,97 dan hasil salah ≈ 0,88. Pada satu foto asli, hasil dengan satu karakter salah tetap bernilai 0,95. Ambang ditentukan setelah ada data asli.
- `confidence` saat ini satu nilai per baris, bukan per karakter.
- Semua teks dikirim sebagai UTF-8.

## Pertanyaan terbuka
1. Batas ukuran upload, ukuran resize di klien, dan format audio.
2. Siapa yang menulis isi `category` dan `explanation`: B dari aturan rarangkén, atau konten dari C?
3. Apakah UI nanti perlu membedakan "dikenali tapi confidence rendah" dari hasil yang yakin? (Bergantung pada data asli; bisa memakai `confidence`.)
4. Satu request satu baris, atau boleh beberapa baris?