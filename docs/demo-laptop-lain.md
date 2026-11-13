# Menjalankan demo AKSARA dari laptop lain

Skenario: yang menyajikan backend bukan laptop pemilik proyek, melainkan laptop teman atau anggota
kelompok lain. Backend tetap berjalan di mesin itu; Cloudflare hanya meneruskan permintaan.

## 1. Yang perlu dikirim

| Kirim | Isi | Catatan |
|---|---|---|
| Akses repo | `git clone https://github.com/nafannn/aksara-app` | kalau repo privat, undang sebagai collaborator; alternatifnya kirim zip tanpa `.venv`, `node_modules`, `vision/data/real` |
| Kredensial tunnel | **hanya jika** ingin URL tetap: `~/.cloudflared/config.yml` + `<id>.json` | kirim pribadi, jangan grup chat — berkas ini setara kunci akun |
| API key | **tidak perlu** | lihat tabel fitur di bagian 4 |

## 2. Rute A — Docker (API saja, langkah paling sedikit)

Butuh Docker Desktop. Image ±2,4 GB, build beberapa menit (unduhan TensorFlow paling lama).

```bash
git clone https://github.com/nafannn/aksara-app && cd aksara-app
docker build -f backend/Dockerfile -t aksara-backend .
docker run -d --name aksara -p 18080:8080 \
  -e AKSARA_CORS_ORIGIN="*" \
  -v aksara-audio:/data/aksara-audio \
  aksara-backend
docker logs -f aksara          # tunggu sampai muncul "Running on"
```

Image ini **tidak memuat frontend**, jadi antarmukanya memakai Vercel dengan override endpoint:

```
https://<app-vercel>/?api=https://<url-tunnel>/api/recognize
```

## 3. Rute B — native (satu URL, termasuk frontend)

Butuh Python 3.12, Node 20+, dan `cloudflared`.

```bash
git clone https://github.com/nafannn/aksara-app && cd aksara-app
python -m venv vision/.venv
vision/.venv/Scripts/pip install -r backend/requirements.txt -r vision/requirements.txt
bash scripts/demo_tunnel.sh
```

Skrip mencetak satu URL HTTPS yang menyajikan frontend **dan** API dari origin yang sama, jadi tidak
ada CORS dan tidak perlu Vercel. Di macOS/Linux ganti `vision/.venv/Scripts/pip` dengan
`vision/.venv/bin/pip`; skrip akan memakai `python` biasa bila venv Windows tidak ditemukan, jadi
pastikan dependensi terpasang di Python itu.

## 4. Tanpa API key

Sudah diuji dengan key dipaksa kosong:

| Fitur | Tanpa key | Dengan key |
|---|---|---|
| Pengenalan aksara (OCR) | ✓ | ✓ |
| Makna dari kamus lokal (SQLite) | ✓ | ✓ |
| Audio untuk 25 kata kamus (dibundel di `backend/audio_seed/`) | ✓ | ✓ |
| Audio untuk kata di luar kamus | ✗ | ✓ |
| Terjemahan makna di luar kamus | ✗ | ✓ |

Artinya demo tanpa key tetap bisa menunjukkan alur lengkap; yang hilang hanya audio dan terjemahan
untuk kata yang tidak ada di kamus. Karena itu `backend/.env` **tidak perlu** dibagikan.

## 5. Memakai tunnel bernama (URL tetap `aksara-api.<domain>`)

Salin dua berkas ke `~/.cloudflared/` di laptop teman, lalu perbaiki path kredensial di `config.yml`
(path di berkas itu absolut milik mesin pemilik):

```yaml
tunnel: 345cff70-7b50-4414-b228-6d5537856a9c
credentials-file: C:\Users\<user-teman>\.cloudflared\345cff70-7b50-4414-b228-6d5537856a9c.json
ingress:
  - hostname: aksara-api.<domain>
    service: http://localhost:18080
  - service: http_status:404
```

`cert.pem` tidak wajib (sudah diuji). Jalankan `bash scripts/demo_tunnel.sh` — skrip membaca
`tunnel:` dan `hostname:` dari config itu. Jangan menyalakan tunnel bernama di dua mesin sekaligus.

## 6. Kalau bermasalah

| Gejala | Sebab dan solusi |
|---|---|
| `address already in use` | port 18080 terpakai; jalankan `AKSARA_DEMO_PORT=19080`, lalu ubah `service:` di config tunnel |
| URL tunnel 502 | backend belum siap; tunggu `curl http://127.0.0.1:18080/healthz` menjawab `ok` |
| Request pertama 7–16 detik | model TensorFlow dimuat saat start; sesudah itu 1–2 detik per foto di CPU |
| Tunnel putus sendiri | laptop sleep atau `cloudflared` berhenti; matikan sleep |
| Frontend Vercel gagal konek | build Vercel memakai `VITE_API_URL` lama; pakai `?api=` atau redeploy |
