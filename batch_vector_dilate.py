#!/usr/bin/env python3
# coding: utf-8
"""
Vectorise des images noir/blanc, crée 3 dilatations (1, 3, 5 mm)
et exporte le tout en SVG et DXF.
"""

import os
import glob
import potrace
import svgwrite
import ezdxf
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from PIL import Image

# Réglage global
INPUT_DIR = "images"
OUTPUT_DIR = "out"
OFFSETS_MM = [0, 1, 3, 5]  # original + dilatations
DPI = 96                   # pour convertir mm → pixels

def mm_to_px(mm):
    return mm / 25.4 * DPI

os.makedirs(OUTPUT_DIR, exist_ok=True)

for path in glob.glob(os.path.join(INPUT_DIR, "*")):
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"➡️ Traitement : {name}")

    # 1️⃣ Charger et binariser
    img = Image.open(path).convert("L")
    bw = img.point(lambda x: 0 if x < 128 else 255, "1")

    # 2️⃣ Vectorisation avec potrace
    bmp = potrace.Bitmap(bw)
    pathlist = bmp.trace()

    # Transformer en géométries Shapely
    shapes = []
    for curve in pathlist:
        pts = [(p.x, p.y) for p in curve.curve]
        if len(pts) > 2:
            shapes.append(Polygon(pts))
    union = unary_union(shapes)

    # 3️⃣ Créer SVG
    svg_path = os.path.join(OUTPUT_DIR, f"{name}.svg")
    dwg = svgwrite.Drawing(svg_path)
    colors = ["black", "gray", "red", "blue"]

    # 4️⃣ DXF
    dxf_path = os.path.join(OUTPUT_DIR, f"{name}.dxf")
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    for i, mm in enumerate(OFFSETS_MM):
        geom = union.buffer(mm_to_px(mm))
        if geom.is_empty:
            continue
        if isinstance(geom, Polygon):
            polys = [geom]
        else:
            polys = geom.geoms

        for poly in polys:
            x, y = poly.exterior.xy
            points = list(zip(x, y))
            # SVG
            dwg.add(dwg.polyline(points, stroke=colors[i], fill="none", stroke_width=0.2))
            # DXF
            msp.add_lwpolyline(points, close=True)

    dwg.save()
    doc.saveas(dxf_path)
    print(f"✅ {name}.svg et {name}.dxf créés.")
