"""Shrink site images and refresh the expedition photo list in index.html.

Run from the repo root after adding or replacing photos:
    python tools/optimize-images.py

- assets/photos/expeditions/*.jpg: longest side capped at 1280 px (re-saved
  only when larger or heavier than ~300 KB), plus a 480 px copy in thumbs/
  for the small photo piles on the map.
- assets/images/expeditions-map.png and assets/photos/proposal/sunset.png:
  converted to .webp (transparency kept); the .png is removed.
- Writes the file list into index.html (EXPEDITION_PHOTO_FILES), so the page
  never has to guess filenames.
"""
import json
import os
import re
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, 'assets', 'photos', 'expeditions')
THUMBS = os.path.join(EXP, 'thumbs')
FULL_MAX, THUMB_MAX = 1280, 480
NAME_RE = re.compile(r'^([A-Za-z]+?)(\d+)\.(jpe?g|png)$', re.I)


def fit(im, side):
    if max(im.size) > side:
        im = im.copy()
        im.thumbnail((side, side), Image.LANCZOS)
    return im


def save_jpeg(im, path, quality):
    im.convert('RGB').save(path, 'JPEG', quality=quality, optimize=True, progressive=True)


def photos():
    os.makedirs(THUMBS, exist_ok=True)
    files = {}
    for name in sorted(os.listdir(EXP)):
        m = NAME_RE.match(name)
        if not m:
            continue
        path = os.path.join(EXP, name)
        im = ImageOps.exif_transpose(Image.open(path))  # bake rotation in before EXIF is dropped
        if max(im.size) > FULL_MAX or os.path.getsize(path) > 300_000:
            save_jpeg(fit(im, FULL_MAX), path, 78)
        thumb = os.path.join(THUMBS, name)
        if not os.path.exists(thumb) or os.path.getmtime(thumb) < os.path.getmtime(path):
            save_jpeg(fit(im, THUMB_MAX), thumb, 72)
        files.setdefault(m.group(1), []).append((int(m.group(2)), name))
    for name in os.listdir(THUMBS):  # drop thumbs whose photo is gone
        if not os.path.exists(os.path.join(EXP, name)):
            os.remove(os.path.join(THUMBS, name))
    # keyed case-insensitively by destination, in number order
    out = {}
    for base, items in files.items():
        out.setdefault(base.lower(), []).extend(items)
    return {k: [n for _, n in sorted(v)] for k, v in sorted(out.items())}


def to_webp(png, side, quality):
    if not os.path.exists(png):
        return
    fit(Image.open(png), side).save(png[:-4] + '.webp', 'WEBP', quality=quality, method=6)
    os.remove(png)


def write_list(listing):
    html_path = os.path.join(ROOT, 'index.html')
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    line = 'var EXPEDITION_PHOTO_FILES = ' + json.dumps(listing, separators=(',', ':')) + ';'
    new, n = re.subn(r'var EXPEDITION_PHOTO_FILES = .*?;(?=\s*// generated)', lambda _: line, html, count=1)
    if n != 1:
        sys.exit('EXPEDITION_PHOTO_FILES line not found in index.html')
    if new != html:
        with open(html_path, 'w', encoding='utf-8', newline='') as f:
            f.write(new)


if __name__ == '__main__':
    listing = photos()
    to_webp(os.path.join(ROOT, 'assets', 'images', 'expeditions-map.png'), 1672, 86)
    to_webp(os.path.join(ROOT, 'assets', 'photos', 'proposal', 'sunset.png'), 2400, 82)
    write_list(listing)
    print(sum(len(v) for v in listing.values()), 'photos listed')
