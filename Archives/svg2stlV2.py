#!/usr/bin/env python3
# coding: utf-8
"""
svg2stl.py
Lit un SVG (1 path), applique 3 dilatations réelles (1, 3, 5 mm),
et génère un SVG de debug.
"""

import numpy as np
import svgwrite
from svgpathtools import svg2paths
from shapely.geometry import Polygon
from config import SVG_OUT_DIR, DEBUG_DIR

DPI = 96
PX_PER_MM = DPI / 25.4
OFFSETS_MM = [1, 3, 5]

DEBUG_DIR.mkdir(parents=True, exist_ok=True)

for svg_file in SVG_OUT_DIR.glob("*.svg"):
    print(f"➡️ {svg_file.name}")

    paths, _ = svg2paths(str(svg_file))
    if len(paths) != 1:
        print(f"⚠️ {svg_file.name} : attend 1 seul path, trouvé {len(paths)}")
        continue
    path = paths[0]

    # Path → polygone fermé
    pts = [path.point(t) for t in np.linspace(0, 1, 500)]
    coords = [(p.real, p.imag) for p in pts]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    base_poly = Polygon(coords)

    if base_poly.is_empty or not base_poly.is_valid:
        print("⚠️ Contour vide ou invalide.")
        continue

    # Dilatations en mm → px
    dilated = [base_poly.buffer(d * PX_PER_MM) for d in OFFSETS_MM]

    # SVG debug
    debug_svg = DEBUG_DIR / f"{svg_file.stem}_debug.svg"
    dwg = svgwrite.Drawing(str(debug_svg))
    x, y = base_poly.exterior.xy
    dwg.add(dwg.polyline(list(zip(x, y)), stroke="black", fill="none", stroke_width=0.5))
    colors = ["red", "orange", "green"]
    for poly, color in zip(dilated, colors):
        x, y = poly.exterior.xy
        dwg.add(dwg.polyline(list(zip(x, y)), stroke=color, fill="none", stroke_width=0.4))
    dwg.save()

    print(f"✅ SVG debug généré : {debug_svg}")
