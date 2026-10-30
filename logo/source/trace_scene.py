"""Trace the scene inside the inner ring of the approved MBR logo into smooth vector layers.

Input: approved raster proof (1100x1100). Output: JSON list of layers
[{name, color, d}] in source pixel coordinates (0..1100), drawn back to front.
"""
import json
import sys
import time

import cv2
import numpy as np
import potrace

src, out_json = sys.argv[1], sys.argv[2]
UP = 3                      # trace at 3x for sub-pixel smooth edges
CX = CY = 550.0
R_SCENE = 371.0             # scene is clipped to this circle in the final SVG

im = cv2.imread(src).astype(np.float32)
H, W = im.shape[:2]

# Canonical colours (hex) for each semantic layer, from k-means of the approved art.
# Order = back to front.
LAYERS = [
    ("sky",            "#ADDBE1"),
    ("bay-line",       "#19517B"),
    ("bay",            "#2271B1"),
    ("grass",          "#188D46"),
    ("road-edge",      "#3F714E"),
    ("road",           "#EDE3C4"),
    ("ridge-outline",  "#493476"),
    ("ridge-1",        "#632C8E"),
    ("ridge-2",        "#77438C"),
    ("ridge-3",        "#9F4C8E"),
    ("trunk-light",    "#835A3D"),
    ("trunk",          "#5C3A18"),
    ("oak-outline",    "#369E6A"),
    ("oak",            "#0D653B"),
    ("car-edge",       "#7F1D26"),
    ("car-shadow",     "#B32A30"),
    ("car",            "#E52123"),
    ("window-glare",   "#7A8B8B"),
    ("window",         "#231F20"),
    ("grille",         "#440F0E"),
]
names = [n for n, _ in LAYERS]
cols_bgr = np.array([[int(h[5:7], 16), int(h[3:5], 16), int(h[1:3], 16)] for _, h in LAYERS], np.float32)

# nearest-colour label per source pixel (inside scene)
yy, xx = np.mgrid[0:H, 0:W]
rr = np.hypot(xx - CX + 0.5, yy - CY + 0.5)
scene = rr < 369
d2 = ((im[:, :, None, :] - cols_bgr[None, None]) ** 2).sum(-1)
lab = d2.argmin(-1)
# pixels outside the scene (gold ring) take the label of nearest scene pixel, so edge layers run under the ring
lab[~scene] = -1
inside = scene.astype(np.uint8)
_, nearest = cv2.distanceTransformWithLabels(1 - inside, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
idx_y, idx_x = np.where(inside)
lut = np.zeros(nearest.max() + 1, np.int64)
lut[nearest[idx_y, idx_x]] = lab[idx_y, idx_x]
lab = lut[nearest]

# crop to the scene box (plus margin) and build a smooth upsampled label map via incremental argmax
x0, y0 = int(CX - R_SCENE - 6), int(CY - R_SCENE - 6)
x1, y1 = int(CX + R_SCENE + 6), int(CY + R_SCENE + 6)
lab_c = lab[y0:y1, x0:x1]
hc, wc = lab_c.shape
best = np.full((hc * UP, wc * UP), -1.0, np.float32)
best_lab = np.zeros((hc * UP, wc * UP), np.int16)
for i in range(len(LAYERS)):
    m = (lab_c == i).astype(np.float32)
    if m.sum() == 0:
        continue
    m = cv2.resize(m, (wc * UP, hc * UP), interpolation=cv2.INTER_CUBIC)
    m = cv2.GaussianBlur(m, (0, 0), 1.6)
    upd = m > best
    best[upd] = m[upd]
    best_lab[upd] = i

# clean tiny specks per layer (anti-aliasing debris) by reassigning to neighbours
def to_svg_path(path, scale, ox, oy):
    parts = []
    f = lambda p: f"{p.x / scale + ox:.2f},{p.y / scale + oy:.2f}"
    for curve in path:
        parts.append("M" + f(curve.start_point))
        for seg in curve:
            if seg.is_corner:
                parts.append("L" + f(seg.c) + "L" + f(seg.end_point))
            else:
                parts.append("C" + f(seg.c1) + " " + f(seg.c2) + " " + f(seg.end_point))
        parts.append("Z")
    return "".join(parts)

layers_out = []
t0 = time.time()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
CAR = ["car-edge", "car-shadow", "car", "window-glare", "window", "grille"]


def fill_holes(m):
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(m)
    cv2.drawContours(out, cs, -1, 1, thickness=cv2.FILLED)
    return out


def trace_mask(m, smooth=None, solid=False):
    """m: uint8 0/1 mask at UP scale. smooth: gaussian sigma (UP px) for blob-like shapes.
    solid: fill interior holes (for body shapes that sit under other details)."""
    if smooth:
        m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), smooth) > 0.5).astype(np.uint8)
    if solid:
        m = fill_holes(m)
    else:
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)    # drop anti-aliasing specks
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)   # fill pinholes
    m = cv2.dilate(m, kernel)       # slight overlap so stacked layers never show hairline gaps
    # potracer treats dark (0) pixels as ink, so pass the inverted mask as an image
    bm = potrace.Bitmap(np.where(m > 0, 0, 255).astype(np.uint8))
    p = bm.trace(turdsize=150, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                 alphamax=1.15, opticurve=True, opttolerance=0.4)
    return to_svg_path(p, UP, x0, y0)


def add(name, color, d):
    layers_out.append({"name": name, "color": color, "d": d})
    print(f"{name:14s} {len(d):7d} chars  {d.count('M'):3d} subpaths  {time.time() - t0:5.1f}s", flush=True)


for i, (name, hexcol) in enumerate(LAYERS):
    if name == "sky" or name in CAR:
        continue                    # sky = base circle in the SVG; car rebuilt below
    m = (best_lab == i).astype(np.uint8)
    if m.sum() < 30:
        continue
    if name == "oak":
        # the dark green also draws the two road edge lines; split them from the canopy
        n_cc, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        canopy = (cc == big).astype(np.uint8)
        lines = ((cc > 0) & (cc != big)).astype(np.uint8)
        add("oak", hexcol, trace_mask(canopy))
        add("road-lines", hexcol, trace_mask(lines))
        continue
    add(name, hexcol, trace_mask(m))

# ---- the 356: stacked smooth shapes, back to front ----
ids = {n: names.index(n) for n in CAR}
isin = lambda ns: np.isin(best_lab, [ids[n] for n in ns]).astype(np.uint8)
gx = np.arange(best_lab.shape[1])[None, :] / UP + x0      # source-px coordinate grids
gy = np.arange(best_lab.shape[0])[:, None] / UP + y0
add("car-shadow", "#B32A30", trace_mask(isin(CAR), smooth=6, solid=True))
add("car", "#E52123", trace_mask(isin(["car", "window", "window-glare", "grille"]), smooth=7, solid=True))
vents = isin(["car-edge"]) * ((gx > 655) & (gy < 860)).astype(np.uint8)
add("car-vents", "#7F1D26", trace_mask(vents, smooth=4))
add("window", "#231F20", trace_mask(isin(["window", "window-glare"]), smooth=4))
add("window-glare", "#8E9A9A", trace_mask(isin(["window-glare"]), smooth=3))

# grille slats: connected components of the darkest red, rebuilt as rounded rectangles
g = (lab == names.index("grille")).astype(np.uint8)
n, cc, stats, _ = cv2.connectedComponentsWithStats(g, connectivity=8)
slats = []
for k in range(1, n):
    x, y, w, h, a = stats[k]
    if a >= 25 and w > 3 * h and 800 < y < 900 and w < 120:
        slats.append((int(x), int(y), int(w), int(h)))
slats.sort(key=lambda s: (s[0] > 550, s[1]))
print("grille slats found:", len(slats))
for sl in slats:
    print("  ", sl)
layers_out.append({"name": "grille", "color": "#3A0D0E", "slats": slats})

json.dump(layers_out, open(out_json, "w"))
print("saved", out_json)
