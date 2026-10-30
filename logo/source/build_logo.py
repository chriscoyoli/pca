"""Build the Monterey Bay Region PCA logo as vector SVG variants.

Geometry is in source pixel units of the approved 1100 x 1100 proof (centre 550, 550).
The scene comes from scene.json (trace_scene.py); rings are true circles; lettering is
Jost set on arcs and converted to outlines, so no font is needed to open the files.
"""
import json
import math
import os

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
CX = CY = 550.0

# Ring radii measured from the approved proof
R_OUTER = 495.0       # outer edge of outer gold ring
R_BAND_OUT = 469.0    # ivory band, outer edge
R_BAND_IN = 391.0     # ivory band, inner edge
R_SCENE = 370.5       # scene circle (inside the inner gold ring)

# ---------- official palette ----------
PRIMARY = {
    "gold": "#DBB04E", "ivory": "#EEECC6", "text": "#684622", "sky": "#AEDDE3", "bay": "#2274B5",
    "ridge-1": "#652D90", "ridge-2": "#77438F", "ridge-3": "#A14C8F", "grass": "#198E47",
    "oak": "#0E663E", "trunk": "#603918", "road": "#EFE3C6", "car": "#E82124",
}
DETAIL = {
    "gold-edge": "#9C7640", "road-lines": "#0E663E", "bay-line": "#19517B", "road-edge": "#3F714E", "ridge-outline": "#493476",
    "trunk-light": "#835A3D", "oak-outline": "#369E6A", "car-shadow": "#B32A30",
    "car-vents": "#7F1D26", "window": "#231F20", "window-glare": "#8E9A9A", "grille": "#3A0D0E",
}
PALETTE = {**PRIMARY, **DETAIL}

TOP_TEXT = "MONTEREY BAY REGION"
BOTTOM_TEXT = "PORSCHE CLUB OF AMERICA"


# ---------- lettering on arcs ----------
class ArcText:
    def __init__(self, font_path):
        self.font = TTFont(font_path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.cap = self.font["OS/2"].sCapHeight
        self.hmtx = self.font["hmtx"]

    def _glyph(self, ch):
        name = self.cmap[ord(ch)]
        adv = self.hmtx[name][0]
        bp = BoundsPen(self.gs)
        self.gs[name].draw(bp)
        return name, adv, bp.bounds  # bounds None for space

    def path(self, text, r_base, a_start, a_end, cap_px, top):
        """Lay text so its ink runs from angle a_start to a_end (degrees, screen coords, y down).
        top=True: letters on the upper arc, baseline on the inner radius, reading clockwise.
        top=False: letters on the lower arc, baseline on the outer radius, reading counter-clockwise."""
        s = cap_px / self.cap
        r_ref = r_base + (cap_px / 2 if top else -cap_px / 2)   # spacing measured at mid-cap radius
        glyphs = [self._glyph(c) for c in text]
        advs = [g[1] * s for g in glyphs]
        lsb = glyphs[0][2][0] * s
        rsb = (glyphs[-1][1] - glyphs[-1][2][2]) * s
        ink_natural = sum(advs) - lsb - rsb
        target = math.radians(abs(a_end - a_start)) * r_ref
        track = (target - ink_natural) / (len(text) - 1)
        sign = 1 if top else -1
        a0 = math.radians(a_start)
        u = -lsb                             # arc position of current glyph's origin
        out = []
        for (name, adv, bounds), w in zip(glyphs, advs):
            centre_u = u + w / 2
            th = a0 + sign * centre_u / r_ref
            px, py = CX + r_base * math.cos(th), CY + r_base * math.sin(th)
            rot = th + (math.pi / 2 if top else -math.pi / 2)
            c, si = math.cos(rot), math.sin(rot)
            # glyph space -> screen: shift so advance centre is x=0, scale and flip y, rotate, translate
            ox = -adv / 2
            a, b = s * c, s * si
            cc, d = s * si, -s * c          # flip y: (x, y) -> (x, -y) before rotation
            e = px + a * ox
            f = py + b * ox
            if bounds is not None:
                pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.2f}")
                self.gs[name].draw(TransformPen(pen, (a, b, cc, d, e, f)))
                out.append(pen.getCommands())
            u += w + track
        return "".join(out)


# ---------- SVG assembly ----------
def ring_gradient():
    stops = [(370, "#8E6F3A"), (373, "#A87B3C"), (377, "#C69844"), (380.5, "#DCB353"), (384, "#C69544"),
             (388, "#A9793C"), (391, "#9C7640"), (469, "#8C6E3A"), (473, "#A8783A"), (478, "#C39641"),
             (482, "#DDB152"), (486, "#C99B47"), (490, "#AE813F"), (495, "#977445")]
    s = "".join(f'<stop offset="{r / R_OUTER:.4f}" stop-color="{c}"/>' for r, c in stops)
    return (f'<radialGradient id="gold" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="{R_OUTER}">'
            f'{s}</radialGradient>')


def annulus(r_out, r_in):
    """Even-odd ring path."""
    def circ(r):
        return (f"M{CX - r:.2f},{CY:.2f}A{r},{r} 0 1 0 {CX + r:.2f},{CY:.2f}"
                f"A{r},{r} 0 1 0 {CX - r:.2f},{CY:.2f}Z")
    return circ(r_out) + circ(r_in)


def build_svg(scene, text_paths, colours, mode="full", title="Monterey Bay Region PCA logo", mirror=False,
              line_art=False):
    """mode: 'full' (metallic gradient rings) or 'flat' (solid spot colours).
    colours: map of layer name -> fill colour (None = omit layer).
    line_art: one-colour outline drawing using colours['ink'] on transparent."""
    vb = f"{CX - R_OUTER - 1:.0f} {CY - R_OUTER - 1:.0f} {2 * R_OUTER + 2:.0f} {2 * R_OUTER + 2:.0f}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{2 * R_OUTER + 2:.0f}" '
           f'height="{2 * R_OUTER + 2:.0f}">', f"<title>{title}</title>", "<defs>",
           f'<clipPath id="scene"><circle cx="{CX}" cy="{CY}" r="{R_SCENE}"/></clipPath>']
    if mode == "full" and not line_art:
        out.append(ring_gradient())
    out.append("</defs>")
    if mirror:
        out.append(f'<g transform="translate({2 * CX} 0) scale(-1 1)">')

    if line_art:
        ink = colours["ink"]
        sw = colours.get("stroke", 5)
        # rings as solid bands, text as solid ink, scene as outlines
        out.append(f'<path fill="{ink}" fill-rule="evenodd" d="{annulus(R_OUTER, R_BAND_OUT)}"/>')
        out.append(f'<path fill="{ink}" fill-rule="evenodd" d="{annulus(R_BAND_IN, R_SCENE)}"/>')
        out.append(f'<g clip-path="url(#scene)" fill="none" stroke="{ink}" stroke-width="{sw}" '
                   f'stroke-linejoin="round">')
        for layer in scene:
            if layer["name"] in colours.get("line_layers", ()):
                out.append(f'<path fill-rule="evenodd" d="{layer["d"]}"/>')
        out.append("</g>")
        out.append(f'<g clip-path="url(#scene)" fill="{ink}">')
        for layer in scene:
            if layer["name"] in colours.get("solid_layers", ()):
                if "slats" in layer:
                    out.append(slats_svg(layer["slats"]))
                else:
                    out.append(f'<path fill-rule="evenodd" d="{layer["d"]}"/>')
        out.append("</g>")
        out.append(f'<path fill="{ink}" d="{text_paths}"/>')
    else:
        gold = "url(#gold)" if mode == "full" else colours["gold"]
        out.append(f'<path fill="{gold}" fill-rule="evenodd" d="{annulus(R_OUTER, R_BAND_OUT)}"/>')
        out.append(f'<path fill="{colours["ivory"]}" fill-rule="evenodd" d="{annulus(R_BAND_OUT, R_BAND_IN)}"/>')
        out.append(f'<path fill="{gold}" fill-rule="evenodd" d="{annulus(R_BAND_IN, R_SCENE - 1)}"/>')
        if mode == "flat" and colours.get("gold-edge"):
            ge = colours["gold-edge"]
            for r in (R_OUTER - 0.9, R_BAND_OUT + 0.9, R_BAND_IN - 0.9, R_SCENE + 0.4):
                out.append(f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{ge}" stroke-width="1.8"/>')
        out.append(f'<g clip-path="url(#scene)">')
        out.append(f'<circle cx="{CX}" cy="{CY}" r="{R_SCENE}" fill="{colours["sky"]}"/>')
        for layer in scene:
            col = colours.get(layer["name"])
            if not col:
                continue
            if "slats" in layer:
                out.append(f'<g fill="{col}">{slats_svg(layer["slats"])}</g>')
            else:
                out.append(f'<path fill="{col}" fill-rule="evenodd" d="{layer["d"]}"/>')
        out.append("</g>")
        out.append(f'<path fill="{colours["text"]}" d="{text_paths}"/>')

    if mirror:
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def slats_svg(slats):
    parts = []
    for x, y, w, h in slats:
        hh = 3.9                      # uniform slat thickness; leaves a clear red gap between slats
        yc = y + h / 2
        parts.append(f'<rect x="{x - 0.4:.1f}" y="{yc - hh / 2:.2f}" width="{w + 0.8:.1f}" height="{hh:.1f}" '
                     f'rx="{hh / 2:.2f}"/>')
    return "".join(parts)


def lettering(weight=700, cap=42.8):
    at = ArcText(os.path.join(HERE, "fonts", f"jost-latin-{weight}-normal.woff2"))
    top = at.path(TOP_TEXT, r_base=409.6, a_start=206.7, a_end=333.0, cap_px=cap, top=True)
    bottom = at.path(BOTTOM_TEXT, r_base=451.8, a_start=173.4, a_end=6.3, cap_px=cap, top=False)
    return top + bottom


def load_scene():
    return json.load(open(os.path.join(HERE, "scene.json")))
