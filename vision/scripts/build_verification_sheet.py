"""Buat lembar verifikasi bernomor dari labels CSV.

    python scripts/build_verification_sheet.py --csv data/real/web/labels_usulan.csv \
        --out data/real/web/verifikasi-plang.png

Tiap baris menampilkan: nama berkas, teks latin, sign_id, usulan label, potongan
baris aksara, sumber, dan lisensi. Kolom ``label`` sengaja tidak ditampilkan
karena itu yang harus diisi manusia setelah memeriksa.

Catatan font: NotoSansSundanese hanya berisi blok U+1B80–U+1BBF, sehingga titik
dan digit digambar dengan font Latin supaya tidak muncul sebagai kotak.
"""
import argparse
import csv
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUN_FONT = os.path.join(ROOT, "fonts", "NotoSansSundanese-Regular.ttf")


def load_font(path, size, fallback="C:/Windows/Fonts/segoeui.ttf"):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(fallback, size)


def draw_mixed(draw, xy, text, sun_font, latin_font, fill):
    """Gambar teks campuran: run non-Sunda memakai font Latin."""
    x, y = xy
    buf, buf_sundanese = "", None
    for ch in text:
        is_sun = 0x1B80 <= ord(ch) <= 0x1BBF or ch == " "
        if buf_sundanese is None:
            buf_sundanese = is_sun
        if is_sun != buf_sundanese and buf:
            font = sun_font if buf_sundanese else latin_font
            draw.text((x, y), buf, font=font, fill=fill)
            x += draw.textlength(buf, font=font)
            buf = ""
        buf_sundanese = is_sun
        buf += ch
    if buf:
        font = sun_font if buf_sundanese else latin_font
        draw.text((x, y), buf, font=font, fill=fill)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--image-root", default=None, help="akar folder gambar (default: folder CSV)")
    args = ap.parse_args()

    root = args.image_root or os.path.dirname(os.path.abspath(args.csv))
    rows = [r for r in csv.DictReader(open(args.csv, encoding="utf-8")) if r.get("file")]
    sun = load_font(SUN_FONT, 40)
    latin_h = load_font("C:/Windows/Fonts/segoeui.ttf", 22)
    latin_s = load_font("C:/Windows/Fonts/segoeui.ttf", 16)

    W, pad = 1150, 16
    tiles = []
    for r in rows:
        path = os.path.join(root, r["file"])
        if not os.path.exists(path):
            print("lewat (tidak ada):", path)
            continue
        im = Image.open(path).convert("RGB")
        im.thumbnail((W, 200))
        tiles.append((r, im))
    if not tiles:
        print("tidak ada gambar yang bisa ditampilkan")
        return 1

    H = pad + sum(96 + im.height + pad for _, im in tiles)
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    y = pad
    for r, im in tiles:
        d.text((pad, y), f'{r["file"]}  ·  {r.get("latin","")}  ·  {r.get("sign_id","")}'
                           f'  ·  {r.get("kondisi","")}', fill="#111", font=latin_h)
        y += 30
        d.text((pad, y + 6), "usulan:", fill="#555", font=latin_s)
        draw_mixed(d, (pad + 78, y - 8), r.get("label_usulan", ""), sun, latin_h, "#0b5d1e")
        status = "TERVERIFIKASI" if r.get("verified") == "yes" else "belum diverifikasi"
        d.text((pad + 560, y + 6), f'({status}; isi kolom label)', fill="#999", font=latin_s)
        y += 40
        sheet.paste(im, (pad, y))
        y += im.height
        src = (r.get("sumber") or "")[:96]
        d.text((pad, y + 2), f'{src}  ·  {r.get("lisensi","")}', fill="#666", font=latin_s)
        y += 26

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    sheet.save(args.out)
    print("lembar:", args.out, sheet.size, "| baris:", len(tiles))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
