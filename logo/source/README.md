# Rebuilding the logo files

These scripts regenerate every file in `logo/` from the board-approved proof.

| File | What it does |
|---|---|
| `approved-proof_2026-10-26.png` | The raster proof the board approved on October 26, 2026 (reference only) |
| `scene-source_board-variant-b.jpg` | The original 1100 x 1100 artwork the scene is traced from |
| `trace_scene.py` | Traces the scene inside the inner ring into smooth vector layers, writes `scene.json` |
| `scene.json` | The traced scene layers (already generated) |
| `build_logo.py` | Geometry, official palette, arc lettering, SVG assembly |
| `export_all.py` | Builds every version and format into an output folder |
| `make_guide.py` | Builds the two-page usage guide PDF |
| `fonts/` | Jost Bold (SIL Open Font License, see `OFL-LICENSE`) |

## Requirements

Python 3 with `cairosvg`, `fonttools`, `brotli`, `potracer`, `opencv-python`, `numpy`, `pillow` and `reportlab`.

```
pip install cairosvg fonttools brotli potracer opencv-python numpy pillow reportlab
```

## Rebuild

```
cd logo/source
python3 export_all.py ../build                       # all versions and formats
python3 make_guide.py ../build/MBR-PCA-Logo-Usage-Guide.pdf ../build
```

Review the output, then copy it over the folders in `logo/`.

`trace_scene.py` only needs to run again if the scene artwork changes:

```
python3 trace_scene.py scene-source_board-variant-b.jpg scene.json
```

The lettering is not traced; `build_logo.py` sets it from scratch at the approved size.

## Notes

- Colors live in `PRIMARY` and `DETAIL` in `build_logo.py`. Change them there, not in the SVG files.
- The lettering is converted to outlines, so the output files need no fonts.
- Adobe Illustrator opens the PDF files directly. Native `.ai` files are not produced.
