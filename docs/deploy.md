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
| `AKSARA_SERVE_FRONTEND` | `1` = backend juga menyajikan `frontend/dist` (mode demo satu URL, lihat bagian 4) |
| `PORT` | Port (default 8080; beberapa host mengatur sendiri) |

Host wajib menyediakan **HTTPS**: kamera di ponsel memblokir permintaan HTTP campuran.

## 2. Railway (tanpa kartu, trial 30 hari)

Cocok kalau verifikasi kartu di Render ditolak.

1. railway.app → **New Project → Deploy from GitHub repo** → pilih repo ini. `railway.toml` sudah menunjuk
   Dockerfile di `backend/Dockerfile` dan health check ke `/healthz`.
2. Tab **Variables**:

   | Variabel | Nilai |
   |---|---|
   | `AKSARA_AUDIO_DIR` | `/data/aksara-audio` |
   | `AKSARA_CORS_ORIGIN` | URL Vercel (isi setelah frontend jadi) |
   | `APIPEDIA_API_KEY` | opsional |
   | `GOOGLE_TRANSLATE_SCRIPT_URL` | opsional |

3. Tab **Settings → Networking → Generate Domain** → dapat `https://xxx.up.railway.app`.
4. `curl https://xxx.up.railway.app/healthz` → `{"status":"ok"}`.

Batas: trial memberi kredit $5 selama 30 hari (sampai 2 vCPU / 1 GB per service, tanpa kartu). Setelah itu
plan Free hanya memberi kredit $1/bulan, jadi service akan berhenti saat kredit habis — cukup untuk periode
tugas, tapi jangan dijadikan hosting permanen.

## 3. Render (perlu verifikasi kartu)

Blueprint `render.yaml` tetap disediakan, tapi Render meminta verifikasi kartu dan sebagian kartu ditolak
tanpa penjelasan. Kalau kamu atau anggota tim punya kartu yang lolos:

1. Render → **New → Blueprint** → pilih repo ini. Blueprint menyetel Docker, plan Free, `AKSARA_AUDIO_DIR`,
   dan health check `/healthz`.
2. Isi variabel yang diminta (boleh dikosongkan): `AKSARA_CORS_ORIGIN`, `APIPEDIA_API_KEY`,
   `GOOGLE_TRANSLATE_SCRIPT_URL`.

Karakter Render free: RAM 512 MB (puncak terukur 237 MB), **tidur setelah 15 menit tanpa trafik**
(~1 menit untuk bangun), disk ephemeral, 750 jam instance/bulan.

## 4. Demo dari laptop: tunnel bernama, URL tetap

Tunnel tetap membuat alamat backend tidak berubah, jadi `VITE_API_URL` di Vercel cukup diisi **sekali**.
Butuh akun Cloudflare dan satu domain yang DNS-nya sudah di Cloudflare.

**Setup sekali:**
```bash
cloudflared tunnel login                                # pilih domain, Authorize
cloudflared tunnel create aksara                        # mencatat id + berkas kredensial
cloudflared tunnel route dns aksara aksara-api.<domain> # membuat CNAME
cp docs/cloudflared-config.example.yml ~/.cloudflared/config.yml   # lalu isi id & hostname
```

**Setiap sesi demo:**
```bash
AKSARA_TUNNEL=aksara \
AKSARA_PUBLIC_URL=https://aksara-api.<domain> \
  bash scripts/demo_tunnel.sh
```

Skrip itu: build frontend dengan API relatif → jalankan backend yang juga menyajikan `frontend/dist`
(`AKSARA_SERVE_FRONTEND=1`) → jalankan tunnel bernama → cetak URL tetapnya. Frontend dan API berada di
origin yang sama, jadi tidak ada CORS. Ctrl+C menghentikan server dan tunnel sekaligus.

Alamat yang dipakai proyek ini: **`https://aksara-api.otwdochub.my.id`** (tunnel `aksara`, id
`345cff70-7b50-4414-b228-6d5537856a9c`).

Batasan: laptop harus hidup dan tidak sleep selama sesi. Kalau laptop mati, URL tetap ada di DNS tetapi
tidak ada yang menjawab.

**Tanpa domain** — Quick Tunnel, URL berubah tiap sesi:

```bash
bash scripts/demo_tunnel.sh          # mencetak https://<acak>.trycloudflare.com
```

### Menjalankan dari laptop lain

Tunnel terikat pada **kredensial**, bukan pada perangkat, jadi laptop teman bisa menyajikan domain
yang sama asalkan punya repo, dependensi (venv Python ±1,8 GB atau image Docker 2,42 GB), dan
`cloudflared`. Ada dua cara:

| Cara | Yang disiapkan | URL |
|---|---|---|
| Quick Tunnel | tidak ada; cukup `cloudflared` | acak, berganti tiap sesi |
| Tunnel bernama (yang dipakai proyek ini) | salin `~/.cloudflared/config.yml` + `<id>.json` | tetap: `aksara-api.<domain>` |

Untuk tunnel bernama, dua berkas itu saja cukup — `cert.pem` tidak perlu, karena `scripts/demo_tunnel.sh`
memanggil tunnel lewat **UUID** (nilai `tunnel:` di config), bukan lewat nama. Sudah diuji dengan
`HOME` diarahkan ke folder kosong yang hanya berisi `config.yml` + `<id>.json`: tunnel tetap mendaftar
empat koneksi. `cloudflared` memang mencetak satu baris
`ERR Cannot determine default origin certificate path`, tetapi baris itu tidak fatal; ia hilang kalau
`cert.pem` ikut disalin atau `origincert` diisi di config.

Jebakan yang paling sering: baris `credentials-file:` di `config.yml` berisi **path absolut** mesin asal
(`C:\Users\USER\.cloudflared\345cff70-….json`). Di laptop teman path itu tidak ada, jadi ubah ke lokasi
berkas di mesinnya:

```yaml
tunnel: 345cff70-7b50-4414-b228-6d5537856a9c
credentials-file: C:\Users\<nama-user-teman>\.cloudflared\345cff70-7b50-4414-b228-6d5537856a9c.json
ingress:
  - hostname: aksara-api.<domain>
    service: http://localhost:18080
  - service: http_status:404
```

Peringatan:

- Berkas kredensial tunnel setara kunci akun: siapa pun yang memegangnya bisa menjalankan tunnel itu.
  Jangan di-commit dan jangan dibagikan di grup chat; Quick Tunnel menghindari ini sepenuhnya.
- Jangan menyalakan tunnel bernama di dua mesin sekaligus — Cloudflare membagi koneksi antar instance,
  sehingga sebagian request mendarat di mesin yang salah dan terasa lebih lambat.
- Port di `service:` harus sama dengan port backend di mesin itu (di proyek ini 18080).
- Laptop yang menjalankan backend harus hidup dan tidak sleep, sama seperti mesin ini.

Kalau frontend sudah ter-deploy di Vercel dan URL backend berubah, tidak perlu build ulang: buka
`https://<app-vercel>/?api=https://<tunnel>/api/recognize`. Query `?api=` menimpa `VITE_API_URL` yang
tertanam saat build (hanya http/https yang diterima).

Cara manual (mis. backend sudah berjalan di Docker):

```bash
docker run -p 8080:8080 -e AKSARA_CORS_ORIGIN="*" aksara-backend
cloudflared tunnel --url http://localhost:8080
```

## 5. Status host lain (dicek November 2026, bisa berubah)

| Host | Catatan |
|---|---|
| Railway | Trial $5/30 hari tanpa kartu (2 vCPU / 1 GB). Plan Free setelahnya hanya $1/bulan kredit |
| Render | Free 512 MB + sleep 15 menit, tapi verifikasi kartu sering menolak |
| Hugging Face Spaces (Docker) | Space Docker/Gradio di `cpu-basic` butuh paket PRO; tanpa itu gagal HTTP 402 |
| Koyeb | Sejak Feb 2026 wajib kartu dengan hold $29 |
| Fly.io | Tanpa free tier; trial 2 jam mesin atau 7 hari, lalu wajib kartu |
| Google Cloud Run | Ada kuota gratis, tapi wajib billing account (kartu) dan disk hanya `/tmp` |

## 6. Frontend (Vercel)

1. Di Vercel: **Add New → Project → Import** repo ini.
2. **Root Directory: `frontend`**, Framework Preset: **Vite** (terdeteksi otomatis).
3. Environment Variables: `VITE_API_URL` = `https://URL-BACKEND-KAMU/api/recognize`.
4. Deploy. Karena `VITE_API_URL` dibaca saat build, kalau URL backend berubah, **redeploy**.

Tidak perlu `vercel.json`.

Catatan Windows: `vercel deploy` lewat CLI di mesin ini gagal dua kali (EPERM symlink di cache
`builders-vlt`, lalu `fetch failed` saat membuat deployment). Deploy lewat dashboard (impor repo) tidak
memakai builder lokal itu, jadi pakai jalur dashboard.

Uji build dengan URL backend sebenarnya sebelum deploy:
```bash
cd frontend
VITE_API_URL=https://URL-BACKEND-KAMU/api/recognize npm run build
npx vite preview --port 4179 --host localhost
```

## 7. Cek setelah deploy
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
