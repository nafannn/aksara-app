# AKSARA Backend

Backend Flask untuk API pengenalan Aksara Sunda. Backend dapat diuji tanpa frontend
dengan mode mock dari modul vision.

## Menjalankan server lokal

Dari folder `aksara-app`:

```powershell
$env:AKSARA_MOCK="1"
python -m backend.app
```

`PYTHONPATH` tidak perlu diatur: `app.py` menambahkan `../vision` ke path secara otomatis.

Server berjalan di `http://127.0.0.1:5000`.

Untuk deployment, set `AKSARA_CORS_ORIGIN` ke origin frontend yang spesifik.

## Audio pengucapan Sunda (APIPedia)

Backend dapat membuat audio secara otomatis dari hasil transliterasi jika API key
APIPedia tersedia. Audio disimpan di `backend/audio` dan dipakai ulang dari cache
pada pemindaian berikutnya.

```powershell
$env:APIPEDIA_API_KEY="apk_isi_dengan_key_kamu"
$env:APIPEDIA_VOICE="su-ID-TutiNeural"
```

`APIPEDIA_VOICE` dapat diganti dengan voice Sunda lain yang tersedia dari endpoint
daftar voice APIPedia. Jika key belum diset atau API gagal, pengenalan tetap
berhasil dan `audio_url` bernilai `null`.

## Makna Bahasa Sunda (Google Apps Script)

Backend memanggil Google Apps Script melalui `POST` dengan body
`{"text": "..."}` dan membaca field `translation` dari responsnya. Isi
`GOOGLE_TRANSLATE_SCRIPT_URL` di `backend/.env`, lalu restart backend. Entri
lokal seperti nama jalan Bandung tetap memakai makna lokal; Google dipakai
untuk kata yang belum ada di database.

`GOOGLE_TRANSLATE_API_KEY` tetap didukung sebagai fallback jika Apps Script
tidak tersedia.

Jika key belum diisi atau Google gagal dihubungi, backend tetap memakai makna
yang sudah tersimpan di database dan tidak menggagalkan proses pengenalan.

## Smoke test tanpa frontend

Cara yang disarankan, dari folder `aksara-app`:

```powershell
$env:PYTHONPATH=".\vision"
python -m backend.smoke_test
```

Alternatifnya, dari folder `backend`:

```powershell
$env:PYTHONPATH="..\vision"
python smoke_test.py
```

Test ini mengirim gambar PNG kecil langsung ke Flask test client dan memeriksa:

- request tanpa gambar menghasilkan HTTP 400;
- gambar valid diproses;
- response memiliki `success`, `aksara`, `latin`, `meaning`, `audio_url`, dan `character_details`
  (skema mengikuti frontend; lihat `docs/api-contract.md`).

## Mengisi kosakata contoh

```powershell
$env:PYTHONPATH="..\vision"
python seed.py
```

Seed awal berisi beberapa kata Sunda umum dan nama jalan/kawasan Bandung.
Nama jalan diberi deskripsi lokasi, bukan terjemahan literal. Daftar ini dapat
diperluas di `seed.py` tanpa mengubah frontend.

Setelah model Role A siap, hapus `AKSARA_MOCK` agar backend memanggil recognizer asli.

## Tes otomatis

Dari folder `backend`:

```powershell
pip install pytest
$env:AKSARA_MOCK="1"
python -m pytest -q tests
```

## Deployment

Lihat `docs/deploy.md`. Ringkasnya: backend dijalankan sebagai Docker (gunicorn), bukan di Vercel,
karena TensorFlow terlalu besar untuk fungsi serverless.

Variabel lingkungan tambahan:

- `AKSARA_AUDIO_DIR`: folder cache audio (default `backend/audio`; otomatis memakai folder
  sementara jika folder itu tidak bisa ditulis).
- `AKSARA_CORS_ORIGIN`: origin frontend yang diizinkan.
- `AKSARA_MAX_UPLOAD_BYTES`: batas ukuran upload (default 8 MB).
