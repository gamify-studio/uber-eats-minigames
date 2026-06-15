#!/usr/bin/env python3
"""Slice the pasted sprite sheet into transparent per-piece PNGs + cell matrices."""
import json
from PIL import Image, ImageDraw
import numpy as np

SRC = "assets/pieces-src.png"
img = Image.open(SRC).convert("RGB")
W, H = img.size
print("image", W, H, "corner", img.getpixel((0, 0)))

# ---- 1. flood-fill the checkerboard background to a sentinel, from many border seeds ----
SENT = (255, 0, 255)
seeds = [(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1),
         (W // 2, 0), (0, H // 2), (W - 1, H // 2), (W // 2, H - 1),
         (5, 5), (W - 6, 5), (5, H - 6), (W - 6, H - 6)]
for s in seeds:
    try:
        ImageDraw.floodfill(img, s, SENT, thresh=55)
    except Exception as e:
        print("seed fail", s, e)

arr = np.asarray(img)
bg = np.all(arr == np.array(SENT), axis=-1)         # True where background
opaque = ~bg
rgba = np.dstack([arr, np.where(bg, 0, 255).astype(np.uint8)])
print("opaque px:", int(opaque.sum()), "of", W * H)

# ---- 2. manual regions (generous; tight-cropped below). x0,y0,x1,y1 ----
REGIONS = {
    "sub":       (40,   85,  850,  430),
    "ubereats":  (860,  30, 1275,  460),
    "banana":    (40,  460,  410, 1040),
    "eggs":      (412, 435,  808, 1040),
    "groceries": (812, 590, 1400, 1040),
}
# Sprites with no legitimate white content: strip ALL near-white pixels to
# transparent (kills enclosed holes the border flood can't reach, e.g. the
# Uber Eats bag handle loop). Do NOT add sub/eggs here — they have real whites.
KILL_WHITE = {"ubereats"}

def tight_bbox(mask, x0, y0, x1, y1):
    sub = mask[y0:y1, x0:x1]
    ys, xs = np.where(sub)
    if len(xs) == 0:
        return None
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)

boxes = {}
for name, (x0, y0, x1, y1) in REGIONS.items():
    bb = tight_bbox(opaque, x0, y0, x1, y1)
    boxes[name] = bb
    print(name, "tight bbox", bb, "size", (bb[2] - bb[0], bb[3] - bb[1]) if bb else None)

# ---- 3. unit scale from the sub (4 cells wide, 1 tall) ----
sb = boxes["sub"]
unit = (sb[2] - sb[0]) / 4.0
print("unit px/cell:", round(unit, 1))

def quantize(name, bb, cov=0.34):
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    cw = max(1, round(w / unit))
    ch = max(1, round(h / unit))
    occ = opaque[y0:y1, x0:x1]
    mat = []
    for r in range(ch):
        row = []
        for c in range(cw):
            cy0 = int(r * h / ch); cy1 = int((r + 1) * h / ch)
            cx0 = int(c * w / cw); cx1 = int((c + 1) * w / cw)
            frac = occ[cy0:cy1, cx0:cx1].mean() if (cy1 > cy0 and cx1 > cx0) else 0
            row.append(1 if frac >= cov else 0)
        mat.append(row)
    return cw, ch, mat

out = {}
full = Image.fromarray(rgba, "RGBA")
for name, bb in boxes.items():
    crop = full.crop(bb)
    if name in KILL_WHITE:
        ca = np.asarray(crop).copy()
        nearwhite = (ca[:, :, 0] > 235) & (ca[:, :, 1] > 235) & (ca[:, :, 2] > 235)
        ca[nearwhite, 3] = 0
        crop = Image.fromarray(ca, "RGBA")
    crop.save(f"assets/{name}.png")
    cw, ch, mat = quantize(name, bb)
    out[name] = {"cells": int(cw), "rows": int(ch), "matrix": mat, "px": [int(bb[2]-bb[0]), int(bb[3]-bb[1])]}
    print(f"\n{name}: {cw}x{ch}")
    for row in mat:
        print("  " + "".join("#" if v else "." for v in row))

with open("assets/pieces.json", "w") as f:
    json.dump(out, f, indent=2)

# ---- 4. debug montage ----
pad = 16
crops = [Image.fromarray(rgba, "RGBA").crop(b) for b in boxes.values()]
mw = sum(c.width for c in crops) + pad * (len(crops) + 1)
mh = max(c.height for c in crops) + pad * 2
mont = Image.new("RGBA", (mw, mh), (40, 40, 40, 255))
x = pad
for c in crops:
    mont.alpha_composite(c, (x, pad))
    x += c.width + pad
mont.convert("RGB").save("assets/_debug.png")
print("\nwrote assets/_debug.png and per-piece PNGs + pieces.json")
