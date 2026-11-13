"""Kumpulkan foto berlisensi CC dari Wikimedia Commons untuk kategori tertentu.

    python scripts/fetch_web_photos.py --out data/real/web/venue \
        --category "Category:Museum Sri Baduga" --category "Category:Gedung Sate"

Menulis thumbnail ke folder keluar, metadata ke <out>/sources.json, dan lembar
kontak <out>/kontak.png bernomor supaya bisa disaring manual.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

UA = {"User-Agent": "AKSARA-student-project/1.0 (https://github.com/nafannn/aksara-app)"}
API = "https://commons.wikimedia.org/w/api.php"


def api(params, tries=3):
    params.update({"format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(6 * (attempt + 1))
                continue
            print("HTTP", e.code)
            return {}
    return {}


def category_files(name, limit=60):
    r = api({"action": "query", "list": "categorymembers", "cmtitle": name,
             "cmtype": "file", "cmlimit": str(limit)})
    time.sleep(1.5)
    return [i["title"] for i in r.get("query", {}).get("categorymembers", [])]


def image_rows(titles):
    rows = []
    ordered = sorted(titles)
    for i in range(0, len(ordered), 12):
        r = api({"action": "query", "titles": "|".join(ordered[i:i + 12]), "prop": "imageinfo",
                 "iiprop": "url|size|extmetadata|mime", "iiurlwidth": "1600"})
        for page in r.get("query", {}).get("pages", []):
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") not in ("image/jpeg", "image/png") or not info.get("url"):
                continue
            meta = info.get("extmetadata", {})
            rows.append({
                "title": page["title"][5:],
                "thumb": info.get("thumburl") or info["url"],
                "w": info.get("width", 0),
                "h": info.get("height", 0),
                "page": info.get("descriptionurl", ""),
                "license": meta.get("LicenseShortName", {}).get("value", "?"),
                "artist": meta.get("Artist", {}).get("value", "")[:80],
            })
        time.sleep(1.5)
    return rows


def contact_sheet(files, out_path, cols=5, tw=330, th=270):
    sheet = Image.new("RGB", (cols * tw, ((len(files) + cols - 1) // cols) * th), "white")
    draw = ImageDraw.Draw(sheet)
    for n, (idx, path) in enumerate(files):
        try:
            im = Image.open(path).convert("RGB")
        except Exception:
            continue
        im.thumbnail((tw - 8, th - 26))
        x, y = (n % cols) * tw + 4, (n // cols) * th + 18
        sheet.paste(im, (x, y))
        draw.text((x, y - 14), f"v{idx:02d}", fill="black")
    sheet.save(out_path)
    return sheet.size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--category", action="append", default=[])
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    titles = set()
    for name in args.category:
        found = category_files(name)
        print(f"{name}: {len(found)}")
        titles.update(found)
    print("total berkas:", len(titles))

    rows = image_rows(titles)
    print("foto:", len(rows))
    os.makedirs(args.out, exist_ok=True)
    json.dump(rows, open(os.path.join(args.out, "sources.json"), "w"), ensure_ascii=False, indent=1)

    ok = []
    for i, row in enumerate(rows[: args.limit]):
        path = os.path.join(args.out, f"v{i:02d}.jpg")
        if not os.path.exists(path):
            try:
                with urllib.request.urlopen(urllib.request.Request(row["thumb"], headers=UA),
                                            timeout=60) as resp, open(path, "wb") as f:
                    f.write(resp.read())
                time.sleep(0.3)
            except Exception as e:
                print(i, "gagal", type(e).__name__)
                continue
        ok.append((i, path))

    sheet_path = os.path.join(args.out, "kontak.png")
    print("kontak:", contact_sheet(ok, sheet_path), "| terunduh:", len(ok), "->", sheet_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
