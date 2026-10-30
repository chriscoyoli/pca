"""Two-page logo usage guide (PDF) for the PCA Monterey Bay Region logo package."""
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

import build_logo as B

out, pkg = sys.argv[1], sys.argv[2]
D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Body", D + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Bold", D + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Ital", D + "DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Bold", italic="Ital", boldItalic="Bold")

BROWN, GOLD, IVORY = colors.HexColor("#684622"), colors.HexColor("#DBB04E"), colors.HexColor("#F7F5E6")
GREY, RULE = colors.HexColor("#5A5A5A"), colors.HexColor("#E3DCC8")
h2 = ParagraphStyle("h2", fontName="Bold", fontSize=11.5, leading=14.5, textColor=BROWN, spaceBefore=8, spaceAfter=4)
body = ParagraphStyle("b", fontName="Body", fontSize=8.8, leading=12)
small = ParagraphStyle("s", parent=body, fontSize=7.8, leading=10.2, textColor=GREY)
cap = ParagraphStyle("c", parent=small, alignment=1)
cell = ParagraphStyle("cl", parent=body, fontSize=7.9, leading=10.2)
cellb = ParagraphStyle("cb", parent=cell, fontName="Bold")
bul = ParagraphStyle("bl", parent=body, leftIndent=11, bulletIndent=0, spaceAfter=2, bulletFontName="Body")
P = lambda t, s=body: Paragraph(t, s)
BL = lambda t: Paragraph(t, bul, bulletText="•")


def grid(data, widths, pad=3):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), IVORY), ("LINEBELOW", (0, 0), (-1, 0), 0.8, GOLD),
                           ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    return t


def cmyk(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    k = 1 - max(r, g, b)
    if k >= 1:
        return "0 / 0 / 0 / 100"
    c, m, y = ((1 - x - k) / (1 - k) for x in (r, g, b))
    return " / ".join(str(round(v * 100)) for v in (c, m, y, k))


def deco(c, doc):
    c.saveState()
    w, h = letter
    c.setFont("Bold", 15); c.setFillColor(BROWN)
    c.drawString(0.75 * inch, h - 0.72 * inch, "PCA Monterey Bay Region Logo: Usage Guide")
    c.setFont("Body", 8.4); c.setFillColor(GREY)
    c.drawString(0.75 * inch, h - 0.95 * inch, "Official logo, approved unanimously by the Board of Directors on "
                                               "October 26, 2026  |  Version 1.0")
    c.setStrokeColor(GOLD); c.setLineWidth(1.2)
    c.line(0.75 * inch, h - 1.12 * inch, w - 0.75 * inch, h - 1.12 * inch)
    c.setStrokeColor(RULE); c.setLineWidth(0.6)
    c.line(0.75 * inch, 0.72 * inch, w - 0.75 * inch, 0.72 * inch)
    c.setFont("Ital", 7.6)
    c.drawString(0.75 * inch, 0.52 * inch, "Files: github.com/chriscoyoli/pca  |  Questions: Chris Coyoli, "
                                           "chris@coyoli.com")
    c.drawRightString(w - 0.75 * inch, 0.52 * inch, f"Page {doc.page} of 2")
    c.restoreState()


doc = BaseDocTemplate(out, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                      topMargin=1.28 * inch, bottomMargin=0.9 * inch,
                      title="PCA Monterey Bay Region Logo: Usage Guide", author="Chris Coyoli")
doc.addPageTemplates([PageTemplate(frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)],
                                   onPage=deco)])
W = doc.width
png = lambda k, sz: f"{pkg}/png/mbr-pca-logo_{k}_{sz}px.png"
S = []

# ---------------- page 1 ----------------
logo = Image(png("full-color", 1024), width=2.35 * inch, height=2.35 * inch)
intro = [
    P("The logo", h2),
    P("A red Porsche 356 drives toward a California live oak, with the Carmel Valley and Big Sur ridgeline and "
      "Monterey Bay beyond. MONTEREY BAY REGION runs across the top and PORSCHE CLUB OF AMERICA across the "
      "bottom, inside a gold ring and ivory band."),
    Spacer(1, 4),
    P("Always use the supplied files. Never redraw, retype or trace the logo from a screenshot.", body),
    Spacer(1, 4),
    P("Which file to use", h2),
    BL("<b>Vendors, printers, signs, enamel badges:</b> SVG, PDF or EPS (vector, scales to any size)."),
    BL("<b>Embroidery:</b> the <i>embroidery</i> version, sent to the digitizer as PDF or SVG."),
    BL("<b>Website, email, slides:</b> PNG with transparent background (JPG if transparency is not "
       "supported)."),
    BL("<b>Window decals applied inside the glass:</b> send the normal file and say it goes inside the glass. "
       "Use the MIRRORED file only if the printer asks for pre-mirrored art."),
]
t = Table([[logo, intro]], colWidths=[2.6 * inch, W - 2.6 * inch])
t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
S.append(t)

S.append(P("Versions", h2))
keys = [("full-color", "Full color", "Primary logo. Metallic gold rings."),
        ("flat-color", "Flat color", "Solid spot colors. Enamel, screen print, vinyl."),
        ("embroidery", "Embroidery", "Fewer colors, no fine lines. Patches, apparel."),
        ("full-color-MIRRORED-for-inside-glass", "Mirrored",
         "Inside-glass decals, only if the printer asks.")]
imgs, caps = [], []
for k, n, d in keys:
    imgs.append(Image(png(k, 4096 if "MIRRORED" in k else 1024), width=1.15 * inch, height=1.15 * inch))
    caps.append(P(f"<b>{n}</b><br/>{d}", cap))
vt = Table([imgs, caps], colWidths=[W / 4] * 4)
vt.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 1), (-1, 1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
S.append(vt)

S.append(P("Official colors", ParagraphStyle("h2c", parent=h2, spaceBefore=4, spaceAfter=3)))
names = [("gold", "Gold rings"), ("ivory", "Ivory band"), ("text", "Lettering"), ("sky", "Sky"),
         ("bay", "Monterey Bay"), ("ridge-1", "Ridge, back"), ("ridge-2", "Ridge, middle"),
         ("ridge-3", "Ridge, front"), ("grass", "Grass"), ("oak", "Live oak"), ("trunk", "Oak trunk"),
         ("road", "Road"), ("car", "356, Guards Red")]
rows = [[P("", cellb), P("Color", cellb), P("HEX", cellb), P("RGB", cellb), P("CMYK (starting values)", cellb)]]
sty = []
for i, (k, n) in enumerate(names, start=1):
    h = B.PRIMARY[k]
    rgb = ", ".join(str(int(h[j:j + 2], 16)) for j in (1, 3, 5))
    rows.append(["", P(n, cell), P(h, cell), P(rgb, cell), P(cmyk(h), cell)])
    sty.append(("BACKGROUND", (0, i), (0, i), colors.HexColor(h)))
ct = grid(rows, [0.35 * inch, 1.55 * inch, 1.0 * inch, 1.2 * inch, W - 4.1 * inch], pad=1.2)
ct.setStyle(TableStyle(sty + [("BOX", (0, 1), (0, -1), 0.4, RULE)]))
S.append(ct)
S.append(P("CMYK values are starting points; match to a printed proof. For paint and enamel, match the 356 to "
           "Porsche Guards Red (paint code 80K). Detail colors are in the SVG files.", small))

# ---------------- page 2 (flows on from the colour note) ----------------
S.append(P("Size and spacing", h2))
sz = [[P("Use", cellb), P("Minimum size", cellb)],
      [P("Full or flat color, print", cell), P("1 inch (25 mm) across", cell)],
      [P("Screen and web", cell), P("120 pixels across (lettering becomes hard to read below this)", cell)],
      [P("Embroidered patch", cell), P("3 inches (76 mm) across; 3.5 inches recommended", cell)],
      [P("Grille badge (enamel)", cell), P("2.75 inches (70 mm) across", cell)]]
S.append(grid(sz, [2.4 * inch, W - 2.4 * inch]))
S.append(Spacer(1, 4))
S.append(P("<b>Clear space:</b> keep other text and graphics at least one tenth of the logo's diameter away "
           "on all sides.", body))

S.append(P("Do not", h2))
for x in ["Stretch, squash, rotate or crop the logo.",
          "Change the colors or convert the logo to black and white.",
          "Add effects such as drop shadows, glows, outlines or bevels.",
          "Retype the lettering or swap the font.",
          "Place the logo on busy photos; use a plain background.",
          "Add Porsche AG marks such as the Porsche crest, the Porsche script or model badges.",
          "Use the earlier versions (the old window sticker, the “P C A” version, or images marked "
          "EXAMPLE). This file set replaces them."]:
    S.append(BL(x))

S.append(P("Decals", h2))
S.append(P("The board supports exploring reverse (static cling) decals and stick-on decals at about the "
           "current size, to be given away or sold for a small charge depending on cost. Notes for the vendor:",
           body))
for x in ["Inside-glass (reverse) decals: the printer usually mirrors the art. A pre-mirrored file is "
          "included if they ask for it.",
          "Print on clear film needs a white underlayer behind the colors so the logo is not see-through.",
          "Ask for a printed proof before the full run."]:
    S.append(BL(x))

S.append(P("Permissions", h2))
S.append(P("This is the Monterey Bay Region's own logo. As noted at the October 26, 2026 board meeting, the "
           "region may use its authorized PCA and Monterey Bay Region logos but must not use artwork outside "
           "the permissions already granted. Vendors may use these files only to produce approved region items.",
           body))

S.append(P("About these files", h2))
S.append(P("Rebuilt as true vector artwork from the board-approved design, with geometric rings and lettering "
           "converted to outlines, so no fonts are needed to open them. The lettering is set in Jost Bold "
           "(SIL Open Font License). The build scripts are in the repository so files can be regenerated.",
           body))

doc.build(S)
print("built", out)
