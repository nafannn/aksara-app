# Kontrak API AKSARA

Versi: **0.4 (DRAFT)**
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
  "meaning_source": "kamus",
  "matched_latin": null,
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
| `meaning_source` | string atau null | B | Asal `meaning`: `"kamus"`, `"mirip"`, `"terjemahan"`, `"bacaan"`, atau `null`. Lihat "Asal makna" di bawah |
| `matched_latin` | string atau null | B | Hanya terisi saat `meaning_source: "mirip"`: kata kamus yang dianggap terdekat |
| `audio_url` | string atau null | B | Path relatif atau URL http(s) ke audio; `null` jika tidak ada |
| `character_details` | array | B | Pemecahan per **gugus aksara** (aksara dasar + rarangkén yang menempel), urut kiri ke kanan |
| `confidence` | number 0–1, *opsional* | **A** | Satu nilai per baris. **Tidak dibaca frontend saat ini**; boleh dikirim untuk dipakai nanti |

Isi tiap elemen `character_details`: `aksara` (gugus, mis. `ᮓᮥ`), `reading` (cara baca, mis. `du`), `category` (jenis, mis. "Rarangkén panyecek"), `explanation` (penjelasan singkat untuk pembelajar).

### Asal makna (`meaning_source`)

`meaning` tidak boleh tampil seolah selalu berasal dari kamus. Nilai yang mungkin:

| Nilai | Arti | Yang harus dilakukan UI |
|---|---|---|
| `kamus` | Cocok persis dengan entri kamus (aksara atau latin) | Tampilkan makna apa adanya |
| `mirip` | Tidak ada di kamus; diambil dari kata terdekat (`matched_latin`, ambang kemiripan 0,75 dan panjang ≥ 4 huruf) | **Wajib menandai** bahwa ini kata terdekat, bukan makna pasti |
| `terjemahan` | Hasil terjemahan otomatis Google | Tandai sebagai terjemahan mesin |
| `bacaan` | Satu gugus aksara; `meaning` berisi bacaannya, bukan arti kata | Tandai sebagai bacaan |
| `null` | Tidak ada makna | Tampilkan "Makna belum tersedia dalam kamus." |

Pencocokan persis selalu menang atas kemiripan. Kata di bawah 4 huruf tidak pernah dicocokkan secara mirip: nama jalan yang salah lebih menyesatkan daripada tidak ada makna.

**Kasus yang perlu ditangani backend**

| Kasus | Respons |
|---|---|
| Dikenali, ada di leksikon | `success: true`, semua field terisi |
| Dikenali, **tidak ada di leksikon** | `success: true`, `aksara`, `latin`, `character_details` terisi; `meaning` dan `audio_url` = `null`. UI menampilkan "Makna belum tersedia dalam kamus." |
| Dikenali, hanya **mirip** kata kamus | `success: true`, `meaning` terisi, `meaning_source: "mirip"`, `matched_latin` berisi kata terdekat. UI wajib menandai bahwa makna berasal dari kata terdekat |
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

`audio_url` hanya diisi kalau berkasnya benar-benar ada di folder cache. Nama berkas deterministik (`tts_<sha256 20 karakter>.mp3` dari voice + teks), jadi tautan tetap sama antar restart **asalkan folder cache persisten** (volume Docker, lihat `docs/deploy.md`). Kalau berkas hilang, backend mengembalikan `null` dan UI menampilkan tombol coba lagi, bukan tautan mati.

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
- Tidak ada perubahan wajib. `normalizeResult()` sudah membaca semua field di atas dan mengabaikan field yang tidak dikenal (`confidence`). `meaning_source` hanya diterima untuk nilai yang dikenal (`kamus`, `mirip`, `terjemahan`, `bacaan`); nilai lain dijadikan `null` supaya tebakan tidak tampil sebagai fakta.
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
