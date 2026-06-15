#!/usr/bin/env python3
"""Detect every piece on the new sheet as a connected component, dump a numbered
montage so we can map index -> piece, then (when ASSIGN is filled) save per-piece PNGs."""
from PIL import Image, ImageDraw
import numpy as np
from collections import deque

SRC = "assets/pieces2-src.png"
img = Image.open(SRC).convert("RGB")
W, H = img.size

# 1. flood white + faint dot-grid bg to a sentinel from border seeds
SENT = (255, 0, 255)
seeds = [(0,0),(W-1,0),(0,H-1),(W-1,H-1),(W//2,0),(0,H//2),(W-1,H//2),(W//2,H-1),(5,5),(W-6,5),(5,H-6),(W-6,H-6)]
for s in seeds:
    try: ImageDraw.floodfill(img, s, SENT, thresh=60)
    except Exception: pass
arr = np.asarray(img)
bg = np.all(arr == np.array(SENT), axis=-1)
opaque = ~bg
rgba = np.dstack([arr, np.where(bg, 0, 255).astype(np.uint8)])

# 2. connected components on a /3 downsample (4-connectivity)
D = 3
small = opaque[::D, ::D]
sh, sw = small.shape
lbl = np.zeros((sh, sw), np.int32)
comps = []
cur = 0
for y in range(sh):
    for x in range(sw):
        if small[y, x] and lbl[y, x] == 0:
            cur += 1
            dq = deque([(y, x)]); lbl[y, x] = cur
            minx = maxx = x; miny = maxy = y; cnt = 0
            while dq:
                cy, cx = dq.popleft(); cnt += 1
                if cx < minx: minx = cx
                if cx > maxx: maxx = cx
                if cy < miny: miny = cy
                if cy > maxy: maxy = cy
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < sh and 0 <= nx < sw and small[ny, nx] and lbl[ny, nx] == 0:
                        lbl[ny, nx] = cur; dq.append((ny, nx))
            if cnt >= 120:  # drop noise
                comps.append({"area": cnt*D*D, "bb": (minx*D, miny*D, (maxx+1)*D, (maxy+1)*D)})

# tighten each bbox on full-res opaque + mean colour
def tight(b):
    x0, y0, x1, y1 = b
    sub = opaque[y0:y1, x0:x1]
    ys, xs = np.where(sub)
    if len(xs) == 0: return None
    return (x0+xs.min(), y0+ys.min(), x0+xs.max()+1, y0+ys.max()+1)
for c in comps:
    c["bb"] = tight(c["bb"])
comps = [c for c in comps if c["bb"]]
# sort top-to-bottom, left-to-right
comps.sort(key=lambda c: (round(c["bb"][1]/120), c["bb"][0]))
full = Image.fromarray(rgba, "RGBA")
for i, c in enumerate(comps):
    x0, y0, x1, y1 = c["bb"]
    reg = arr[y0:y1, x0:x1][opaque[y0:y1, x0:x1]]
    col = reg.mean(axis=0).astype(int) if len(reg) else [0,0,0]
    c["i"] = i; c["col"] = tuple(col)
    print(f"#{i}: bb={c['bb']} size=({x1-x0}x{y1-y0}) area={c['area']} rgb={tuple(col)}")

# numbered montage (grid)
cols = 5
cw = max(c["bb"][2]-c["bb"][0] for c in comps) + 14
chh = max(c["bb"][3]-c["bb"][1] for c in comps) + 28
rows = (len(comps)+cols-1)//cols
mont = Image.new("RGBA", (cols*cw, rows*chh), (35,35,40,255))
dr = ImageDraw.Draw(mont)
for c in comps:
    r, cc = divmod(c["i"], cols)
    ox, oy = cc*cw+7, r*chh+22
    mont.alpha_composite(full.crop(c["bb"]), (ox, oy))
    dr.text((cc*cw+6, r*chh+4), f"#{c['i']}", fill=(255,255,0,255))
mont.convert("RGB").save("assets/_comps.png")
print(f"\n{len(comps)} components -> assets/_comps.png")

# index -> piece (from the numbered montage)
ASSIGN = {0: "ubereats", 1: "bigbag", 8: "nana", 9: "toast", 11: "toilet"}
KILL_WHITE = {"ubereats", "bigbag"}  # green bags: strip enclosed handle-hole white
for c in comps:
    name = ASSIGN.get(c["i"])
    if not name:
        continue
    crop = full.crop(c["bb"])
    if name in KILL_WHITE:
        ca = np.asarray(crop).copy()
        nw = (ca[:, :, 0] > 235) & (ca[:, :, 1] > 235) & (ca[:, :, 2] > 235)
        ca[nw, 3] = 0
        crop = Image.fromarray(ca, "RGBA")
    crop.save(f"assets/{name}.png")
    print("saved", name, "->", c["bb"])
