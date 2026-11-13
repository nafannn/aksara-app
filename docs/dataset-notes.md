# Catatan dataset foto plang (vision/data/real)

Dokumen ini menjelaskan kebijakan pelabelan dan provenance data asli. Foto aslinya **tidak
di-commit** (lihat `.gitignore` dan aturan data di `README.md`); yang ikut repo hanya
`labels.csv` dan dokumen ini.

## Kebijakan label

1. **Label = apa yang tercetak di plang, apa adanya.** Jangan menormalkan ke bentuk baku,
   jangan membetulkan ejaan, jangan menambahkan kata yang tidak terlihat. Model belajar
   transkripsi visual, bukan pengetahuan bahasa.
2. **Label diisi manusia, bukan mesin.** Usulan otomatis (transliterator atau tebakan) hanya
   boleh ada di kolom `label_usulan`. Baris dengan `verified != yes` tidak dipakai training.
3. **Satu baris = satu crop baris aksara**, yaitu citra yang benar-benar masuk model — bukan
   foto plang utuh.
4. `sign_id` menandai plang fisik. Split train/val/test dilakukan **per `sign_id`**, bukan per
   foto, supaya dua foto plang yang sama tidak jatuh di train dan test sekaligus.

## Kolom `labels.csv`

| Kolom | Isi |
|---|---|
| `file` | path crop relatif terhadap `vision/data/real/` |
| `latin` | teks latin di plang (untuk manusia, bukan target model) |
| `sign_id` | id plang fisik; dipakai untuk split |
| `kondisi` | siang / malam / miring / dekat / jauh |
| `varian_awalan` | bentuk penulisan "JL" pada plang: `jl-singkat`, `jalan`, atau `tanpa-awalan` |
| `label` | transkripsi aksara (diisi manusia) |
| `label_usulan` | usulan mesin, boleh salah |
| `verified` | `yes` hanya setelah diperiksa pembaca aksara |
| `sumber`, `lisensi`, `catatan` | provenance dan hal yang perlu diingat |

## Varian penulisan awalan (temuan lapangan)

Plang jalan tidak seragam menulis "JL":

| Plang | Bentuk di plang | Terbaca |
|---|---|---|
| JL. BRAGA | `ᮏ᮪ ᮜ᮪.` — dua aksara masing-masing dengan pamaéh | "j.l." |
| JL. BANDA | ditulis sebagai kata penuh | "jalan" |

Konsekuensi yang harus disadari:

- Transliterasi Latin ikut berbeda ("jl. braga" vs "jalan banda"), sehingga pencarian kamus
  bisa gagal pada salah satu bentuk. Penyeragaman ("JL" → nama jalan) adalah keputusan
  lapisan aplikasi, bukan tugas OCR.
- Evaluasi sebaiknya dipecah per `varian_awalan`; akurasi keseluruhan bisa menyesatkan kalau
  satu varian jauh lebih sering muncul.
- Dataset harus memuat kedua varian, karena keduanya nyata di jalan.

## Kondisi yang perlu seimbang

`kondisi` dicatat agar laporan bisa memecah CER per kondisi. Usahakan tiap plang punya
minimal dua kondisi (mis. siang dekat + malam atau miring), bukan 30 foto plang yang sama
pada satu kondisi.

## Provenance

- Wikimedia Commons: lisensi CC BY / CC BY-SA tercatat di kolom `lisensi`; atribusi wajib
  bila dataset atau model dipakai di luar repo.
- Foto pengguna: milik sendiri, tanpa batasan lisensi.
- Foto dari blog/Instagram tidak dipakai walau teksnya bisa diverifikasi — lisensinya tidak
  jelas.

## Baseline model pada data asli (6 crop, 5 plang)

Diukur dengan `scripts/evaluate.py --real_csv data/real/labels.csv` memakai model
`models/aksara_crnn.keras` yang dilatih hanya dengan data sintetis:

| Plang | Confidence | CER | Hasil |
|---|---|---|---|
| BANDA | 0,948 | **0,000** | `ᮏᮜᮔ᮪ ᮘᮔ᮪ᮓ` tepat |
| Cilaki | 0,831 | 0,522 | separuh benar |
| Cimanuk (foto 1) | 0,694 | 0,667 | salah |
| Braga | 0,678 | 0,875 | salah |
| Cimanuk (foto 2) | 0,640 | 1,750 | salah |
| Bahureksa | 0,508 | 1,923 | salah |

Agregat: **CER 0,9481**, akurasi kata **1/6**. Bandingkan dengan CER 0,0539 pada test
sintetis — selisih ini adalah domain gap, bukan regresi kode.

Yang perlu dicatat saat menulis laporan: kegagalannya **tidak seragam**. Plang BANDA
terbaca tepat, jadi model tidak buta terhadap foto asli; yang gagal adalah plang dengan
tipografi dekoratif (huruf jalan) yang tidak pernah dilihat model. Confidence juga bukan
ambang tolak: satu sampel yang tepat bernilai 0,948, tetapi sampel salah ada di 0,83
(Cilaki) — lebih tinggi daripada beberapa yang salah total.

`n = 6` hanya cukup untuk menunjukkan arah, bukan untuk menyimpulkan akurasi sistem.
Angka ini adalah baseline "sebelum", bukan hasil akhir.

Setelah 10 sampel tambahan dari arsip pengguna diverifikasi (campuran tulisan tangan, render
digital, dan foto plang), angka yang diperbarui pada **n = 16**:

| Metrik | Nilai |
|---|---|
| CER | **0,9304** |
| Akurasi kata | 2/16 (0,125) |
| Confidence rata-rata (benar) | 0,9738 |
| Confidence rata-rata (salah) | 0,6729 |

Dua yang tepat: plang BANDA dan kartu `ᮠᮁᮒ` (harta) — keduanya memakai bentuk huruf yang
dekat dengan Noto. Menarik bahwa `harta` hanya 5 karakter, jadi keberhasilan pada kata pendek
tidak berarti model paham struktur rarangkén.

## Eksperimen augmentasi (20 epoch, 3000 gambar sintetis)

Dua model dilatih dengan resep identik (3000 train / 300 val, 20 epoch, lr 2e-3,
seed sama) — bedanya hanya augmentasi:

| Model | Augmentasi | CER sintetis-test | Kata sintetis | CER foto asli (n=6) |
|---|---|---|---|---|
| `aksara_crnn.keras` | (dataset lama, ±12.000 gambar) | **0,0534** | 0,773 | 0,9481 |
| `exp_basic.keras` | jitter kecerahan saja | 0,1678 | 0,478 | 0,7922 |
| `exp_strong.keras` | + erosi/dilasi stroke, blur, skala horizontal, noise | 0,2023 | 0,370 | **0,7532** |

Kesimpulan:

1. **Augmentasi tipografi benar-benar membantu foto asli**, dari CER 0,7922 ke 0,7532
   pada dataset dan epoch yang sama. Efeknya konsisten, bukan kebetulan.
2. **Harganya nyata**: CER sintetis naik 0,1678 → 0,2023. Model jadi kurang jago pada
   font yang dipakai untuk membuat data latih.
3. **Belum cukup.** CER 0,75 pada foto asli tetap tidak terpakai; akurasi kata tetap 1/6.
   Augmentasi tidak bisa menggantikan data asli.
4. Model lama unggul di sintetis (0,0534) karena dilatih dengan jauh lebih banyak gambar,
   tetapi paling buruk di foto asli (0,9481) — indikasi kuat overfit ke Noto Sans Sundanese.

Dua batas yang terlihat dari eksperimen ini: ukuran kanvas 32×192 (detail rarangkén hilang
pada kata 12+ gugus) dan volume data. Keduanya perlu diubah bersama, bukan salah satu saja.

## Label literal vs bentuk baku

Plang kadang menulis bentuk yang tidak baku (mis. "jala.dra." untuk "jl. dr.", atau
menyisipkan `ᮃ` sehingga terbaca "kosaasiha"). Dataset menyimpan dua kolom:

| Kolom | Isi | Dipakai untuk |
|---|---|---|
| `label` | transkripsi **literal** dari yang tercetak | training & evaluasi |
| `label_baku` | bentuk yang seharusnya menurut kaidah | analisis, bukan target model |

Untuk `jl. achmad sobana` label literalnya belum dicatat (pembaca baru mengisi bentuk
baku), jadi `label_baku` terisi sementara `catatan` menandai hal ini.

Contoh nyata dari arsip: `jl. rd. kosasih kel. cikaret` di plang terbaca
"jala.dra. kosaasiha kela. cikaareta" — bukan penulisan yang benar, tetapi itulah yang
harus dipelajari model.

## Status

Per November 2026: 5 sumber berbeda (Cimanuk, Bahureksa, Braga, Banda, frasa Cilaki) dan 6
crop, semuanya sudah diverifikasi pembaca aksara. Masih jauh di bawah kebutuhan ±20–30 plang
untuk fine-tune yang bisa dipertanggungjawabkan.
