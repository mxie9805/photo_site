#!/usr/bin/env python3
"""Build the photo site.

    python build.py            build into dist/
    python build.py --serve    build, then preview at http://localhost:8000

Inputs
    photos/        exported JPEGs (any size; they are resized for the web)
    photos.csv     optional details per photo: title, series, place, ...
    site.toml      site name, about text, series list

Outputs
    dist/                  the website
    dist/data/photos.csv   every photo with its merged details, for analysis
"""

from __future__ import annotations

import csv
import datetime as dt
import functools
import http.server
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, ImageOps

ROOT = Path(__file__).parent
PHOTOS = ROOT / "photos"
DIST = ROOT / "dist"
WIDTHS = (800, 1600, 2400)          # widths of the web copies, in px
WEBP_QUALITY = 82
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
CSV_FIELDS = ["file", "title", "title_zh", "series", "place", "place_zh", "date",
              "featured", "note", "note_zh", "camera", "lens", "focal_length",
              "aperture", "shutter", "iso", "film"]
EXIF_FIELDS = ["camera", "lens", "focal_length", "aperture", "shutter", "iso", "film"]


# ---------------------------------------------------------------- helpers

def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "photo"


def is_yes(value: str) -> bool:
    return value.strip().lower() in {"yes", "y", "true", "1", "x"}


def clean(value) -> str:
    """EXIF strings often carry trailing NULs and spaces."""
    return str(value).replace("\x00", "").strip() if value is not None else ""


def as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def tidy_number(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- EXIF

def read_exif(path: Path) -> dict:
    """Shooting details stored inside the file. Missing values come back as ''."""
    out = {key: "" for key in EXIF_FIELDS} | {"date": ""}
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            sub = exif.get_ifd(0x8769)          # the Exif sub-directory
    except Exception:                            # unreadable metadata is not fatal
        return out

    make, model = clean(exif.get(0x010F)), clean(exif.get(0x0110))
    if model:
        first = make.split()[0].lower() if make else ""
        out["camera"] = model if first and model.lower().startswith(first) else f"{make} {model}".strip()

    out["lens"] = clean(sub.get(0xA434))

    focal = as_float(sub.get(0x920A))
    if focal:
        out["focal_length"] = f"{tidy_number(focal)}mm"

    fnumber = as_float(sub.get(0x829D))
    if fnumber:
        out["aperture"] = f"f/{tidy_number(fnumber)}"

    exposure = as_float(sub.get(0x829A))
    if exposure:
        if exposure >= 1:
            out["shutter"] = f"{tidy_number(exposure)}s"
        else:
            out["shutter"] = f"1/{round(1 / exposure)}s"

    iso = sub.get(0x8827)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None
    if iso:
        out["iso"] = clean(iso)

    taken = clean(sub.get(0x9003) or exif.get(0x0132))
    match = re.match(r"(\d{4}):(\d{2}):(\d{2})(?:\s+(\d{2}):(\d{2}))?", taken)
    if match and match.group(1) != "0000":
        out["date"] = "-".join(match.group(1, 2, 3))
        if match.group(4):
            out["date"] += f" {match.group(4)}:{match.group(5)}"
    return out


# ---------------------------------------------------------------- images

def make_web_images(src: Path, slug: str, out_dir: Path) -> dict:
    """Write resized WebP copies; return their names, widths and the photo's shape."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        width, height = im.size
        widths = sorted({w for w in WIDTHS if w < width} | {min(width, max(WIDTHS))})
        sources = []
        for w in widths:
            name = f"{slug}-{w}.webp"
            target = out_dir / name
            sources.append({"file": name, "width": w})
            if target.exists() and target.stat().st_mtime >= src.stat().st_mtime:
                continue
            h = round(height * w / width)
            resized = im.resize((w, h), Image.Resampling.LANCZOS) if w != width else im.copy()
            if resized.mode not in ("RGB", "RGBA"):
                resized = resized.convert("RGB")
            # Keep the colour profile, drop everything else (location, serial numbers).
            resized.save(target, "WEBP", quality=WEBP_QUALITY, method=6,
                         icc_profile=im.info.get("icc_profile"))
    return {"sources": sources, "width": width, "height": height}


# ---------------------------------------------------------------- loading

def load_rows() -> dict[str, dict]:
    path = ROOT / "photos.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = {}
        for row in csv.DictReader(handle):
            name = (row.get("file") or "").strip()
            if name:
                rows[name] = {k: (v or "").strip() for k, v in row.items() if k}
        return rows


def load_photos(site: dict, img_dir: Path) -> list[dict]:
    rows = load_rows()
    files = sorted(p for p in PHOTOS.iterdir() if p.suffix.lower() in IMAGE_TYPES)
    on_disk = {p.name for p in files}
    for missing in sorted(set(rows) - on_disk):
        print(f"  note: photos.csv lists {missing}, but it is not in photos/")

    known_series = {s["slug"] for s in site.get("series", [])}
    csv_order = {name: i for i, name in enumerate(rows)}
    photos, slugs = [], set()

    for path in files:
        row = rows.get(path.name, {})
        exif = read_exif(path)
        slug = base = slugify(path.stem)
        n = 2
        while slug in slugs:
            slug, n = f"{base}-{n}", n + 1
        slugs.add(slug)

        series = slugify(row.get("series", "")) if row.get("series") else ""
        if series and series not in known_series:
            print(f"  note: {path.name} uses series '{series}', which is not in site.toml")
            series = ""

        photo = {
            "file": path.name,
            "slug": slug,
            "title": row.get("title") or path.stem.replace("-", " ").replace("_", " "),
            "title_zh": row.get("title_zh", ""),
            "series": series,
            "place": row.get("place", ""),
            "place_zh": row.get("place_zh", ""),
            "place_slug": slugify(row["place"]) if row.get("place") else "",
            "note": row.get("note", ""),
            "note_zh": row.get("note_zh", ""),
            "featured": is_yes(row.get("featured", "")),
            "date": row.get("date") or exif["date"],
            "order": csv_order.get(path.name, len(csv_order)),
        }
        photo["year"] = photo["date"][:4] if re.match(r"\d{4}", photo["date"]) else ""
        for key in EXIF_FIELDS:                      # the CSV wins over the file
            photo[key] = row.get(key) or exif[key]
        photo.update(make_web_images(path, slug, img_dir))
        photos.append(photo)

    dated = sorted((p for p in photos if p["date"]), key=lambda p: p["date"], reverse=True)
    undated = sorted((p for p in photos if not p["date"]), key=lambda p: (p["order"], p["file"]))
    ordered = dated + undated
    for i, photo in enumerate(ordered):
        photo["newer"] = ordered[i - 1]["slug"] if i > 0 else ""
        photo["older"] = ordered[i + 1]["slug"] if i + 1 < len(ordered) else ""
    return ordered


def build_series(site: dict, photos: list[dict]) -> list[dict]:
    by_file = {p["file"]: p for p in photos}
    out = []
    for entry in site.get("series", []):
        members = [p for p in photos if p["series"] == entry["slug"]]
        if not members:
            continue
        years = sorted({p["year"] for p in members if p["year"]})
        span = years[0] if len(years) == 1 else f"{years[0]}–{years[-1]}" if years else ""
        out.append({
            "slug": entry["slug"],
            "name": entry.get("name") or entry["slug"],
            "name_zh": entry.get("name_zh", ""),
            "count": len(members),
            "years": span,
            "cover": by_file.get(entry.get("cover", "")) or members[0],
        })
    return out


def build_places(photos: list[dict]) -> list[dict]:
    places: dict[str, dict] = {}
    for p in photos:
        if p["place_slug"]:
            place = places.setdefault(p["place_slug"], {
                "slug": p["place_slug"], "name": p["place"], "name_zh": p["place_zh"], "count": 0})
            place["count"] += 1
            place["name_zh"] = place["name_zh"] or p["place_zh"]
    return sorted(places.values(), key=lambda x: x["name"])


# ---------------------------------------------------------------- output

def write_data(photos: list[dict], series: list[dict]) -> None:
    data_dir = DIST / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    names = {s["slug"]: s["name"] for s in series}
    fields = ["file", "title", "series", "place", "date", "year", "camera", "lens",
              "focal_length", "aperture", "shutter", "iso", "film", "width", "height", "featured"]
    rows = [{**{k: p[k] for k in fields}, "series": names.get(p["series"], "")} for p in photos]
    with (data_dir / "photos.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (data_dir / "photos.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def build() -> None:
    site = tomllib.loads((ROOT / "site.toml").read_text(encoding="utf-8"))
    site.setdefault("links", {})
    site.setdefault("about", {})
    site["year"] = dt.date.today().year

    img_dir = DIST / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    (DIST / "p").mkdir(exist_ok=True)

    photos = load_photos(site, img_dir)
    series = build_series(site, photos)
    places = build_places(photos)
    by_slug = {p["slug"]: p for p in photos}
    by_file = {p["file"]: p for p in photos}
    featured = [p for p in photos if p["featured"]] or photos
    site["about"]["portrait_photo"] = by_file.get(site["about"].get("portrait", ""))

    # Remove web images and pages for photos that no longer exist.
    keep = {s["file"] for p in photos for s in p["sources"]}
    for stale in img_dir.glob("*.webp"):
        if stale.name not in keep:
            stale.unlink()
    for stale in (DIST / "p").glob("*.html"):
        if stale.stem not in by_slug:
            stale.unlink()

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    series_names = {s["slug"]: s for s in series}
    common = dict(site=site, photos=photos, series=series, places=places,
                  series_names=series_names, by_slug=by_slug)

    def render(template: str, target: str, **context) -> None:
        root = "../" * target.count("/")
        html = env.get_template(template).render(root=root, **common, **context)
        (DIST / target).write_text(html, encoding="utf-8")

    render("home.html", "index.html", page="home", featured=featured)
    render("photos.html", "photos.html", page="photos")
    render("series.html", "series.html", page="series")
    render("about.html", "about.html", page="about")
    for photo in photos:
        render("photo.html", f"p/{photo['slug']}.html", page="photo", photo=photo)

    shutil.copytree(ROOT / "static", DIST / "static", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("")
    write_data(photos, series)
    print(f"Built {len(photos)} photos, {len(series)} series, {len(places)} places -> {DIST}")


def serve(port: int = 8000) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    print(f"Preview at http://localhost:{port}  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
