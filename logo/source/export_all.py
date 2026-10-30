"""Generate all logo variants and file formats into an output folder.

Usage: python3 export_all.py OUT_DIR
"""
import io
import os
import sys

import cairosvg
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


def render_png(svg, size):
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(data)).convert("RGBA")


variants = {}
variants["full-color"] = B.build_svg(SCENE, TEXT, FULL, mode="full",
                                     title="PCA Monterey Bay Region logo, full color")
variants["flat-color"] = B.build_svg(SCENE, TEXT, FLAT, mode="flat",
                                     title="PCA Monterey Bay Region logo, flat spot color")
variants["embroidery"] = B.build_svg(SCENE, TEXT, EMB, mode="flat",
                                     title="PCA Monterey Bay Region logo, simplified for embroidery")
variants["full-color-MIRRORED-for-inside-glass"] = B.build_svg(
    SCENE, TEXT, FULL, mode="full", mirror=True,
    title="PCA Monterey Bay Region logo, full color, MIRRORED for inside-glass decals")

PNG_SIZES = {
    "full-color": [4096, 2048, 1024, 512, 256],
    "flat-color": [4096, 2048, 1024],
    "embroidery": [4096, 2048, 1024],
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
