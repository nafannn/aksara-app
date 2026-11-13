# Panduan Deploy AKSARA

Skema yang dipakai: **frontend di Vercel, backend sebagai Docker di host lain.**
Backend tidak dideploy di Vercel karena TensorFlow terlalu besar untuk fungsi serverless:
`site-packages` terpasang **1,8 GB** (TensorFlow 1,5 GB, OpenCV 111 MB, NumPy 24 MB), sedangkan batas
fungsi Python di Vercel 500 MB (5 GB lewat Large Functions beta). Tambahan lagi: body request dibatasi
4,5 MB sementara backend menerima sampai 8 MB, dan filesystem fungsi read-only selain `/tmp`.

```
Ponsel → Vercel (frontend, HTTPS) ──POST /api/recognize──► Backend Docker (HTTPS)
                                                            └─ Flask + model TensorFlow + SQLite
```

## 0. Angka yang sudah diukur

Diukur dari image yang di-build dari repo ini, container dibatasi `--memory=512m`:

| Ukuran | Nilai |
|---|---|
| Ukuran image Docker | 2,42 GB |
| Puncak memori proses (cgroup `memory.peak`, model dimuat + inferensi) | **237 MB** |
| Request pertama setelah container restart (termasuk muat model) | **2,4 s** di mesin dev |
| Audio bawaan untuk 25 kata kamus | 624 KB |

Kesimpulan: instance **512 MB sudah cukup**, jadi Render free bisa dipakai. Angka 2,4 s itu di mesin dev
dengan CPU penuh; di vCPU 0,5 milik host gratis, permintaan pertama bisa jauh lebih lama.

## 1. Backend (Docker)

Dari **root repo**:
```bash
docker build -f backend/Dockerfile -t aksara-backend .
docker run -p 8080:8080 -e AKSARA_CORS_ORIGIN="*" aksara-backend
curl http://localhost:8080/healthz
curl -F "image=@contoh.png;type=image/png" http://localhost:8080/api/recognize
```

Bila host menyediakan disk persisten, pasang sebagai volume agar audio kata **di luar kamus** ikut bertahan:

```bash
docker run -p 8080:8080 -e AKSARA_CORS_ORIGIN="*" \
  -v aksara-audio:/data/aksara-audio aksara-backend
docker run --rm -v aksara-audio:/data/aksara-audio -e AKSARA_AUDIO_DIR=/data/aksara-audio \
  -e APIPEDIA_API_KEY=apk_isi_dengan_key_kamu aksara-backend python -m backend.pregenerate_audio
```

Audio untuk **kata yang sudah ada di kamus tidak butuh volume maupun API key**: 25 berkasnya ikut
dibundel di `backend/audio_seed/` dan disalin ke `AKSARA_AUDIO_DIR` setiap proses start. Volume hanya
menambah daya tahan untuk kata di luar kamus yang pernah disintesis.

Variabel lingkungan:

| Variabel | Fungsi |
|---|---|
| `AKSARA_CORS_ORIGIN` | Origin frontend yang diizinkan. Di produksi isi URL Vercel (mis. `https://aksara.vercel.app`), bukan `*` |
| `APIPEDIA_API_KEY`, `APIPEDIA_VOICE` | Audio TTS (opsional) |
| `GOOGLE_TRANSLATE_SCRIPT_URL` | Arti kata (opsional) |
| `AKSARA_AUDIO_DIR` | Folder cache audio (default `backend/audio`; isi `/data/aksara-audio` saat memakai volume Docker) |
| `AKSARA_TTS_TIMEOUT` | Batas tunggu panggilan TTS dalam detik (default 5). Lewat batas → `audio_url: null`, pengenalan tetap berhasil |
| `PORT` | Port (default 8080; beberapa host mengatur sendiri) |

Host wajib menyediakan **HTTPS**: kamera di ponsel memblokir permintaan HTTP campuran.

## 2. Render (jalur gratis yang sudah diukur muat)

1. Render → **New → Blueprint** → pilih repo ini. `render.yaml` di root sudah menyetel Docker, plan
   Free, `AKSARA_AUDIO_DIR`, dan health check ke `/healthz`.
2. Isi variabel yang diminta (boleh dikosongkan): `AKSARA_CORS_ORIGIN`, `APIPEDIA_API_KEY`,
   `GOOGLE_TRANSLATE_SCRIPT_URL`.
3. Setelah deploy, `curl https://URL-RENDER/healthz` harus menjawab `{"status":"ok"}`.

Karakter Render free: RAM 512 MB (puncak terukur 237 MB), **tidur setelah 15 menit tanpa trafik**
(~1 menit untuk bangun), disk ephemeral, 750 jam instance/bulan. Sebelum sidang, buka URL backend sekali
supaya container tidak dingin.

## 3. Status host lain (dicek November 2026, bisa berubah)

| Host | Catatan |
|---|---|
| Hugging Face Spaces (Docker) | Space Docker/Gradio di hardware `cpu-basic` sekarang **butuh paket PRO**; tanpa itu pembuatan gagal HTTP 402. RAM 16 GB, disk tidak persisten, Space pause setelah 48 jam idle |
| Render | Free 512 MB + sleep 15 menit. Instance berbayar mulai $7/bln (0,5 CPU/512 MB) |
| Google Cloud Run | Ada kuota gratis, tapi disk hanya `/tmp`; untuk audio perlu mount bucket |
| Fly.io / Railway | Perlu akun + metode bayar |

## 4. Frontend (Vercel)

1. Di Vercel: **Add New → Project → Import** repo ini.
2. **Root Directory: `frontend`**, Framework Preset: **Vite** (terdeteksi otomatis).
3. Environment Variables: `VITE_API_URL` = `https://URL-BACKEND-KAMU/api/recognize`.
4. Deploy. Karena `VITE_API_URL` dibaca saat build, kalau URL backend berubah, **redeploy**.

Tidak perlu `vercel.json`.

Uji build dengan URL backend sebenarnya sebelum deploy:
```bash
cd frontend
VITE_API_URL=https://URL-BACKEND-KAMU/api/recognize npm run build
npx vite preview --port 4179 --host localhost
```

## 5. Cek setelah deploy
- `curl https://URL-BACKEND/healthz` → `{"status":"ok"}`.
- `curl -F "image=@contoh.png;type=image/png" https://URL-BACKEND/api/recognize` → ada `aksara`, `latin`,
  `audio_url`.
- Buka URL Vercel di ponsel, pindai satu crop aksara.
- Jika muncul "Server belum dapat memproses foto": cek `AKSARA_CORS_ORIGIN`, cek `VITE_API_URL`, lalu log backend.
- Jika hasil muncul tetapi audio tidak berbunyi: wajar di host tanpa API key untuk kata di luar kamus;
  UI menampilkan "Audio pengucapan belum tersedia."

## Keterbatasan yang diketahui
- **Render free tidur** setelah 15 menit tanpa trafik. Permintaan pertama menunggu container bangun
  (±1 menit) ditambah muat model. Paling terasa saat demo — buka URL backend lebih dulu.
- **Disk ephemeral di host gratis.** Kata di luar kamus yang pernah disintesis kehilangan audionya saat
  restart; kata kamus aman karena berkasnya dibundel di image (`backend/audio_seed/`).
- **Permintaan pertama lambat** karena model dimuat saat pemanggilan pertama (2,4 s di mesin dev).
- **Dockerfile sudah diuji build** (image 2,42 GB) dan dijalankan dengan `--memory=512m`: inferensi
  berhasil, puncak 237 MB, `/healthz` menjawab.
- Semua di Vercel baru mungkin kalau model dikonversi ke format ringan (ONNX/TFLite) dan preprocessing
  ditulis ulang; hasilnya harus dievaluasi ulang, jadi itu proyek tersendiri.
