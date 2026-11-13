# AKSARA Frontend

UI mobile web (React + Vite) untuk memindai Aksara Sunda, melihat hasil, dan belajar per karakter.

## Menjalankan
```bash
cd frontend
npm ci
cp .env.example .env     # atur VITE_API_URL jika backend tidak di 127.0.0.1:5000
npm run dev
```
Backend lokal: lihat `backend/README.md` (mode mock: `AKSARA_MOCK=1`).

## Skrip
- `npm run dev`: server pengembangan
- `npm run build`: build produksi
- `npm run lint`: ESLint
- Tes: `node --test "src/**/*.test.js"`

## Catatan
- Kamera di ponsel butuh HTTPS (`getUserMedia` mensyaratkan secure context). `localhost` dikecualikan.
- Skema respons API: `docs/api-contract.md`.
- Deploy: `docs/deploy.md`.
