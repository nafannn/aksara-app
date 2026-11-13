# AKSARA

AKSARA adalah aplikasi web mobile untuk mengenali dan mempelajari Aksara Sunda dari foto tulisan di ruang publik.

Pengguna dapat mengambil atau mengunggah foto, memotong bagian tulisan, lalu melihat hasil pengenalan dalam bentuk:

- karakter Aksara Sunda;
- transliterasi Latin;
- penjelasan setiap gugus aksara dan rarangkén;
- makna dalam Bahasa Indonesia;
- audio pengucapan Bahasa Sunda; dan
- riwayat hasil pemindaian.

## Cara kerja

```text
Foto tulisan
    ↓
Crop satu baris aksara
    ↓
Model CRNN-CTC mengenali karakter Unicode Aksara Sunda
    ↓
Backend mentransliterasi dan mencari makna
    ↓
Frontend menampilkan hasil, pembelajaran karakter, dan audio
```

## Arsitektur

| Bagian | Teknologi | Peran |
| --- | --- | --- |
| Frontend | React + Vite | Kamera, crop foto, hasil scan, pembelajaran karakter, dan riwayat |
| Backend | Flask + Gunicorn | API pengenalan, transliterasi, kamus, audio, dan CORS |
| Model | TensorFlow/Keras + OpenCV | Mengenali satu baris Aksara Sunda dari gambar |
| Penyimpanan | SQLite | Menyimpan kosakata dan metadata audio |
| Terjemahan | Google Apps Script | Menerjemahkan kata Sunda yang belum ada di kamus |
| Audio | APIPedia TTS | Membuat audio pengucapan Bahasa Sunda secara opsional |

## Menjalankan secara lokal

### Prasyarat

- Python 3.12
- Node.js dan npm
- Git

TensorFlow digunakan oleh modul vision, jadi Python 3.12 direkomendasikan untuk mengikuti environment project.

### 1. Menyiapkan backend

Dari root repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt -r vision\requirements.txt
Copy-Item backend\.env.example backend\.env
python -m backend.app
```

Backend berjalan di `http://127.0.0.1:5000`.

Isi `backend/.env` jika ingin mengaktifkan fitur tambahan:

```env
APIPEDIA_API_KEY=your_apipedia_key
APIPEDIA_VOICE=su-ID-TutiNeural
GOOGLE_TRANSLATE_SCRIPT_URL=https://script.google.com/macros/s/your_deployment_id/exec
```

API key dan file `.env` bersifat rahasia. Jangan commit file `.env` ke repository.

### 2. Menyiapkan frontend

Buka terminal baru dari root repository:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Frontend biasanya tersedia di `http://localhost:5173` dan menggunakan backend lokal melalui:

```env
VITE_API_URL=http://127.0.0.1:5000/api/recognize
```

Jika backend menggunakan URL publik, ganti nilai `VITE_API_URL` dengan endpoint lengkap backend tersebut.

### Mode mock

Untuk mencoba alur aplikasi tanpa memuat model TensorFlow:

```powershell
$env:AKSARA_MOCK="1"
python -m backend.app
```

Hapus environment variable tersebut untuk menggunakan model asli.

## Endpoint utama

```http
POST /api/recognize
Content-Type: multipart/form-data
```

Field yang dikirim adalah `image` dalam format JPEG atau PNG. Backend mengembalikan hasil pengenalan, transliterasi, makna, detail karakter, confidence, dan `audio_url` jika audio tersedia.

Dokumentasi lengkap tersedia di [docs/api-contract.md](docs/api-contract.md).

## Deployment

Backend dideploy sebagai Docker web service karena membutuhkan TensorFlow dan OpenCV. Konfigurasi deployment yang tersedia:

- [Render Blueprint](render.yaml)
- [Railway configuration](railway.toml)
- [Panduan deployment lengkap](docs/deploy.md)

Untuk membangun dan menjalankan container secara lokal:

```bash
docker build -f backend/Dockerfile -t aksara-backend .
docker run --rm -p 8080:8080 \
  -e AKSARA_CORS_ORIGIN="*" \
  aksara-backend
```

Frontend dapat dideploy sebagai static site. Setelah backend memiliki URL publik, set:

```env
VITE_API_URL=https://nama-backend-kamu.example/api/recognize
```

### Mengganti backend tanpa build ulang

Frontend mendukung override endpoint melalui query string:

```text
https://nama-frontend-kamu.example/?api=https%3A%2F%2Fnama-backend-kamu.example%2Fapi%2Frecognize
```

Fitur ini berguna untuk mengganti backend demo atau URL Cloudflare Tunnel sementara.

## Struktur repository

```text
.
├── backend/       Flask API, SQLite, transliterasi, audio, dan Dockerfile
├── frontend/      React + Vite mobile web app
├── vision/        preprocessing, model TensorFlow, dan recognizer
├── docs/          kontrak API dan panduan deployment
├── render.yaml    konfigurasi Render Blueprint
└── railway.toml   konfigurasi Railway
```

## Pengujian

Smoke test backend tanpa frontend:

```powershell
$env:AKSARA_MOCK="1"
python -m backend.smoke_test
```

Validasi frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Batasan saat ini

- Input model harus berupa crop satu baris Aksara Sunda; deteksi otomatis dari foto plang utuh belum tersedia.
- Model baseline terutama dilatih dan dievaluasi pada data sintetis.
- Foto dengan tipografi dekoratif, pencahayaan buruk, atau sudut miring dapat menurunkan akurasi.
- Audio dan terjemahan bergantung pada layanan eksternal jika kata belum tersedia secara lokal.

## Dokumentasi

- [Kontrak API](docs/api-contract.md)
- [Panduan deployment](docs/deploy.md)
- [Dokumentasi backend](backend/README.md)
- [Dokumentasi modul vision](vision/README.md)
