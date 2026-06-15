#!/usr/bin/env python3
"""Slice the standalone parcel + shampoo screenshots: flood the EXTERIOR white to
transparent (interior whites — 'Parcel' text, shampoo label — are enclosed by the
black tile border so the flood never reaches them), then tight-crop to the art."""
from PIL import Image, ImageDraw
import numpy as np

JOBS = [
    ("assets/shampoo-src.png", "assets/shampoo.png"),
    ("assets/parcel-src.png",  "assets/parcel.png"),
]
SENT = (255, 0, 255)

for src, out in JOBS:
    img = Image.open(src).convert("RGB")
    W, H = img.size
    seeds = [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1),
             (W // 2, 0), (0, H // 2), (W - 1, H // 2), (W // 2, H - 1),
             (3, 3), (W - 4, 3), (3, H - 4), (W - 4, H - 4)]
    for s in seeds:
        try:
            ImageDraw.floodfill(img, s, SENT, thresh=60)
        except Exception:
            pass
    arr = np.asarray(img)
    bg = np.all(arr == np.array(SENT), axis=-1)
    rgba = np.dstack([arr, np.where(bg, 0, 255).astype(np.uint8)])
    # tight crop to opaque
    op = ~bg
    ys, xs = np.where(op)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = Image.fromarray(rgba[y0:y1, x0:x1], "RGBA")
    crop.save(out)
    print(f"{out}: {crop.size}  (from {src} {W}x{H})")
