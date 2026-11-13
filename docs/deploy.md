# Panduan Deploy AKSARA

Skema yang dipakai: **frontend di Vercel, backend sebagai Docker di host lain.**
Backend tidak dideploy di Vercel karena TensorFlow terlalu besar untuk fungsi serverless
(terpasang ±1,3 GB; batas fungsi Python di Vercel 500 MB).

```
Ponsel → Vercel (frontend, HTTPS) ──POST /api/recognize──► Backend Docker (HTTPS)
                                                            └─ Flask + model TensorFlow + SQLite
```

## 1. Backend (Docker)

Dari **root repo**:
```bash
docker build -f backend/Dockerfile -t aksara-backend .
docker run -p 8080:8080 -e AKSARA_CORS_ORIGIN="*" aksara-backend
curl -F "image=@contoh.png;type=image/png" http://localhost:8080/api/recognize
```
Variabel lingkungan:

| Variabel | Fungsi |
|---|---|
| `AKSARA_CORS_ORIGIN` | Origin frontend yang diizinkan. Di produksi isi URL Vercel (mis. `https://aksara.vercel.app`), bukan `*` |
| `APIPEDIA_API_KEY`, `APIPEDIA_VOICE` | Audio TTS (opsional) |
| `GOOGLE_TRANSLATE_SCRIPT_URL` | Arti kata (opsional) |
| `AKSARA_AUDIO_DIR` | Folder cache audio (default `/tmp/aksara_audio` di Docker) |
| `PORT` | Port (default 8080; beberapa host mengatur sendiri) |

Pilih host yang bisa menjalankan Docker dan punya **RAM minimal ±1 GB**. Saat diukur di sandbox, satu
proses yang memuat model memakai puncak ±620 MB, jadi paket 512 MB kemungkinan tidak cukup.
Pilihan yang umum: Hugging Face Spaces (Docker), Render, Railway, Fly.io, Google Cloud Run.
Aku belum membandingkan atau mencoba satu pun dari host itu; cek kuota gratis dan RAM mereka sebelum memilih.
Host harus menyediakan **HTTPS** (kamera di ponsel dan browser memblokir permintaan campuran HTTP/HTTPS).

## 2. Frontend (Vercel)

1. Di Vercel: **Add New → Project → Import** repo ini.
2. **Root Directory: `frontend`**, Framework Preset: **Vite** (terdeteksi otomatis).
3. Environment Variables: `VITE_API_URL` = `https://URL-BACKEND-KAMU/api/recognize`.
4. Deploy. Karena `VITE_API_URL` dibaca saat build, kalau URL backend berubah, **redeploy**.

Tidak perlu `vercel.json`.

## 3. Cek setelah deploy
- Buka URL Vercel di ponsel, pindai satu foto crop aksara.
- Jika muncul "Server belum dapat memproses foto": cek `AKSARA_CORS_ORIGIN`, cek URL di `VITE_API_URL`,
  lalu lihat log backend.

## Keterbatasan yang diketahui
- **Audio TTS bersifat sementara.** Cache audio ada di disk sementara; setelah backend restart, berkas lama
  hilang dan tautan audio dari riwayat lama bisa 404. Untuk produksi sungguhan perlu penyimpanan permanen.
- **Permintaan pertama lambat** karena model dimuat saat pemanggilan pertama.
- **Dockerfile belum diuji build** (tidak ada Docker di lingkungan tempat aku menguji). Yang sudah diuji:
  gunicorn dengan `backend.app:app` berjalan dan memberi respons benar dengan model asli.
- Jika ingin semuanya di Vercel, model harus dikonversi ke format ringan (mis. ONNX + `onnxruntime`).
  Itu pekerjaan tambahan dan hasilnya harus diverifikasi ulang.
