"""Generate all logo variants and file formats into an output folder.

Usage: python3 export_all.py OUT_DIR
"""
import io
import os
import re
import sys

import cairosvg
import cv2
import numpy as np
import potrace
from PIL import Image

import build_logo as B

OUT = sys.argv[1]
SCENE = B.load_scene()
TEXT = B.lettering(700)
NAME = "mbr-pca-logo"
os.makedirs(OUT, exist_ok=True)
for sub in ("svg", "pdf", "eps", "png", "jpg", "favicon"):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)

FULL = {**B.PALETTE}
FLAT = {**B.PALETTE}

# Embroidery / simplified: merge fine detail colours into neighbours, no gradients, no hairlines
EMB = {**B.PALETTE}
EMB.update({
    "bay-line": B.PRIMARY["bay"], "road-edge": B.PRIMARY["grass"], "ridge-outline": B.PRIMARY["ridge-1"],
    "trunk-light": B.PRIMARY["text"], "trunk": B.PRIMARY["text"], "oak-outline": B.PRIMARY["oak"],
    "window-glare": B.DETAIL["window"], "grille": B.DETAIL["window"], "car-vents": B.DETAIL["car-shadow"],
    "road": B.PRIMARY["ivory"], "gold-edge": None,
})


def to_gray(svg):
    def g(m):
        h = m.group(1)
        r, gg, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        y = round(0.299 * r + 0.587 * gg + 0.114 * b)
        return f"#{y:02X}{y:02X}{y:02X}"
    return re.sub(r"#([0-9A-Fa-f]{6})\b", g, svg)


def render_png(svg, size):
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def one_colour_paths():
    """True single-colour artwork: draw rings, text and scene outlines in black over white 'paper'
    knockouts, rasterise at high resolution, and trace back to one clean compound path."""
    ink = "#000000"
    vb = f"{B.CX - B.R_OUTER - 1:.0f} {B.CY - B.R_OUTER - 1:.0f} {2 * B.R_OUTER + 2:.0f} {2 * B.R_OUTER + 2:.0f}"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">',
             f'<defs><clipPath id="s"><circle cx="{B.CX}" cy="{B.CY}" r="{B.R_SCENE}"/></clipPath></defs>',
             f'<rect x="0" y="0" width="1100" height="1100" fill="#fff"/>',
             f'<path fill="{ink}" fill-rule="evenodd" d="{B.annulus(B.R_OUTER, B.R_BAND_OUT)}"/>',
             f'<path fill="{ink}" fill-rule="evenodd" d="{B.annulus(B.R_BAND_IN, B.R_SCENE)}"/>',
             '<g clip-path="url(#s)" stroke-linejoin="round">']
    by = {l["name"]: l for l in SCENE}
    W = "#fff"

    def fill(name, colour):
        parts.append(f'<path fill="{colour}" fill-rule="evenodd" d="{by[name]["d"]}"/>')

    def outline(names, w):
        """Outer outline of a group of shapes: thick stroke, then refill to erase the inner half and
        any internal seams, leaving a clean line of width w around the group."""
        for n in names:
            parts.append(f'<path fill="{W}" stroke="{ink}" stroke-width="{2 * w}" fill-rule="evenodd" '
                         f'd="{by[n]["d"]}"/>')
        for n in names:
            fill(n, W)

    # back to front; nearer shapes hide farther lines
    fill("bay-line", ink)                       # horizon line
    outline(["grass"], 1.5)                     # shoreline where the grass meets the bay
    fill("road", W)
    fill("road-lines", ink)                     # the two road edge lines
    for n in ("ridge-1", "ridge-2", "ridge-3"):
        fill(n, W)
    fill("ridge-outline", ink)                  # ridge outlines exactly as drawn in the art
    outline(["trunk", "trunk-light"], 1.7)
    fill("oak-outline", ink)                    # canopy outline
    fill("oak", W)
    outline(["car-shadow"], 1.9)                # car silhouette
    parts.append(f'<path fill="none" stroke="{ink}" stroke-width="1.6" d="{by["car"]["d"]}"/>')
    fill("car-vents", ink)
    fill("window", ink)
    fill("window-glare", W)
    parts.append(f'<g fill="{ink}">{B.slats_svg(by["grille"]["slats"])}</g>')
    parts.append("</g>")
    parts.append(f'<path fill="{ink}" d="{TEXT}"/>')
    parts.append("</svg>")
    svg = "".join(parts)
    S = 4000
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=S, output_height=S, background_color="white")
    g = np.array(Image.open(io.BytesIO(data)).convert("L"))
    bm = potrace.Bitmap(np.where(g < 128, 0, 255).astype(np.uint8))
    p = bm.trace(turdsize=20, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0,
                 opticurve=True, opttolerance=0.2)
    sc = (2 * B.R_OUTER + 2) / S
    o = B.CX - B.R_OUTER - 1
    f = lambda pt: f"{pt.x * sc + o:.2f},{pt.y * sc + o:.2f}"
    d = []
    for c in p:
        d.append("M" + f(c.start_point))
        for s in c:
            d.append(("L" + f(s.c) + "L" + f(s.end_point)) if s.is_corner else
                     ("C" + f(s.c1) + " " + f(s.c2) + " " + f(s.end_point)))
        d.append("Z")
    return "".join(d)


def one_colour_svg(d, colour, title):
    vb = f"{B.CX - B.R_OUTER - 1:.0f} {B.CY - B.R_OUTER - 1:.0f} {2 * B.R_OUTER + 2:.0f} {2 * B.R_OUTER + 2:.0f}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{2 * B.R_OUTER + 2:.0f}" '
            f'height="{2 * B.R_OUTER + 2:.0f}"><title>{title}</title>'
            f'<path fill="{colour}" fill-rule="evenodd" d="{d}"/></svg>')


variants = {}
variants["full-color"] = B.build_svg(SCENE, TEXT, FULL, mode="full",
                                     title="PCA Monterey Bay Region logo, full color")
variants["flat-color"] = B.build_svg(SCENE, TEXT, FLAT, mode="flat",
                                     title="PCA Monterey Bay Region logo, flat spot color")
variants["embroidery"] = B.build_svg(SCENE, TEXT, EMB, mode="flat",
                                     title="PCA Monterey Bay Region logo, simplified for embroidery")
variants["grayscale"] = to_gray(variants["full-color"]).replace("full color", "grayscale")
mono = one_colour_paths()
variants["one-color-black"] = one_colour_svg(mono, "#000000", "PCA Monterey Bay Region logo, one color black")
variants["one-color-white"] = one_colour_svg(mono, "#FFFFFF", "PCA Monterey Bay Region logo, one color white")
variants["full-color-MIRRORED-for-inside-glass"] = B.build_svg(
    SCENE, TEXT, FULL, mode="full", mirror=True,
    title="PCA Monterey Bay Region logo, full color, MIRRORED for inside-glass decals")

PNG_SIZES = {
    "full-color": [4096, 2048, 1024, 512, 256],
    "flat-color": [4096, 2048, 1024],
    "embroidery": [4096, 2048, 1024],
    "grayscale": [2048, 1024],
    "one-color-black": [4096, 2048, 1024],
    "one-color-white": [4096, 2048, 1024],
    "full-color-MIRRORED-for-inside-glass": [4096],
}

for key, svg in variants.items():
    base = f"{NAME}_{key}"
    open(os.path.join(OUT, "svg", base + ".svg"), "w").write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=os.path.join(OUT, "pdf", base + ".pdf"))
    cairosvg.svg2eps(bytestring=svg.encode(), write_to=os.path.join(OUT, "eps", base + ".eps"))
    for sz in PNG_SIZES[key]:
        render_png(svg, sz).save(os.path.join(OUT, "png", f"{base}_{sz}px.png"), optimize=True)
    print("built", key)

# JPGs on white for email / Office / vendors that cannot take transparency
for key in ("full-color", "flat-color"):
    im = render_png(variants[key], 2048)
    bg = Image.new("RGB", im.size, "white")
    bg.paste(im, mask=im.split()[3])
    bg.save(os.path.join(OUT, "jpg", f"{NAME}_{key}_2048px_white-background.jpg"), quality=93)

# Favicons / app icons from the flat version (crisper at tiny sizes)
fav = render_png(variants["flat-color"], 1024)
for sz, fname in [(16, "favicon-16x16.png"), (32, "favicon-32x32.png"), (180, "apple-touch-icon.png"),
                  (192, "android-chrome-192x192.png"), (512, "android-chrome-512x512.png")]:
    fav.resize((sz, sz), Image.LANCZOS).save(os.path.join(OUT, "favicon", fname), optimize=True)
fav.resize((64, 64), Image.LANCZOS).save(os.path.join(OUT, "favicon", "favicon.ico"),
                                          sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("done")
