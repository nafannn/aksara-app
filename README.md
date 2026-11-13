# AKSARA

Sistem multimedia untuk mengenali dan mempelajari Aksara Sunda dari foto plang di fasilitas publik.
Proyek II4050 Rekayasa Sistem Multimedia, Kelompok 3 (ITB, STI).

Alur: foto crop baris aksara → pengenalan aksara (Unicode) → transliterasi Latin → arti kata → audio pengucapan.
Arsitektur: client-server mobile web application (ponsel sebagai klien, server Flask sebagai pemroses).

## Struktur repo
```
aksara-app/
├── README.md
├── docs/
│   └── api-contract.md   # kontrak API antar bagian (baca sebelum coding)
├── vision/               # Peran A: dataset sintetis, preprocessing, model, recognize()
├── backend/              # Peran B: API Flask, transliterator, SQLite, audio
└── frontend/             # Peran C: UI mobile web, cropper, evaluasi pengguna
```

| Folder | Pemilik | Status |
|---|---|---|
| `vision/` | A | Pipeline dan model baseline jalan; foto plang asli berlabel belum ada |
| `backend/` | B | API Flask, transliterator, SQLite; skema respons sesuai `docs/api-contract.md` v0.3 |
| `frontend/` | C | UI mobile web; terhubung ke API lewat `VITE_API_URL` |

## Persiapan
- **Python 3.12** (TensorFlow belum mendukung 3.14). Disarankan memakai venv per folder.
- Jangan commit `.venv/`, `node_modules/`, atau berkas `.env`.

### vision/
```powershell
cd vision
uv venv --python 3.12 .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
python scripts/evaluate.py --synth test   # perlu dataset dulu: python scripts/make_dataset.py
```
Detail lengkap ada di `vision/README.md`.

### backend/ memanggil vision
Paket Python-nya bernama `aksara` dan berada di `vision/`. Dari folder `backend/`:
```powershell
$env:PYTHONPATH="..\vision"            # PowerShell
# export PYTHONPATH=../vision          # Mac/Linux
$env:AKSARA_MOCK="1"                   # jawaban tetap, jika model belum jalan di mesin ini
```
Contoh pemakaian ada di `docs/api-contract.md`.

## Cara kerja bertiga (Git)
- Sebelum mulai kerja: `git pull`
- Setelah selesai: `git add .` → `git commit -m "pesan singkat"` → `git push`
- Edit foldermu sendiri; perubahan di `docs/api-contract.md` harus diberi tahu ke semua.
- Jika `git pull` menampilkan `CONFLICT`, jangan di-force; selesaikan bersama.

## Aturan data
- **Foto plang asli tidak di-commit.** Simpan di folder bersama (Drive); commit hanya `vision/data/real/labels.csv`.
- **Test set dipisah sejak awal** dan tidak dipakai untuk tuning atau pelatihan. Split berdasarkan plang, bukan berdasarkan foto (`vision/scripts/split_real.py`).
- Tidak ada angka akurasi dari data sintetis di laporan sebagai akurasi sistem.
- Repo ini **private**; foto ruang publik bisa memuat wajah atau plat nomor.

## Dokumen terkait
- `docs/api-contract.md`: kontrak API
- `vision/README.md`: modul pengenalan aksara
- `docs/deploy.md`: cara men-deploy frontend dan backend
