#!/usr/bin/env python3
# coding: utf-8
"""
Étape 1 : Conversion des images noir/blanc → SVG vectorisés (OpenCV + Shapely)
Utilise config.py pour les chemins et paramètres globaux
"""

import cv2
import numpy as np
import svgwrite
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from config import (
    IMAGES_DIR, SVG_OUT_DIR, DEBUG_DIR,
    THRESHOLD, MIN_AREA_PX, USE_APPROX, APPROX_EPSILON,
    USE_SMOOTH, SMOOTH_BUFFER
)

# 📁 Prépare les dossiers
for d in [SVG_OUT_DIR, DEBUG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

for path in IMAGES_DIR.glob("*"):
    name = path.stem
    print(f"➡️ Traitement : {name}")

    # Lecture et binarisation
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"⚠️ Impossible de lire {path}")
        continue
    _, bw = cv2.threshold(img, THRESHOLD, 255, cv2.THRESH_BINARY_INV)

    # Détection des contours externes
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    shapes, filtered_contours = [], []

    for c in contours:
        if cv2.contourArea(c) > MIN_AREA_PX:
            if USE_APPROX:
                c = cv2.approxPolyDP(c, epsilon=APPROX_EPSILON, closed=True)
            pts = [(float(x), float(y)) for [[x, y]] in c]
            if len(pts) > 2:
                poly = Polygon(pts)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if USE_SMOOTH:
                    poly = poly.buffer(SMOOTH_BUFFER, join_style=2).buffer(-SMOOTH_BUFFER, join_style=2)
                if not poly.is_empty:
                    shapes.append(poly)
                    filtered_contours.append(c)

    if not shapes:
        print(f"⚠️ Aucun contour valide pour {name}")
        continue

    try:
        union = unary_union(shapes)
    except Exception as e:
        print(f"⚠️ Erreur d'union pour {name}: {e}")
        union = MultiPolygon(shapes)

    # Debug image
    debug_img = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(debug_img, filtered_contours, -1, (0, 0, 255), 1)
    cv2.imwrite(str(DEBUG_DIR / f"{name}_contours.png"), debug_img)

    # Export SVG
    dwg = svgwrite.Drawing(str(SVG_OUT_DIR / f"{name}.svg"), profile="tiny")
    polys = [union] if isinstance(union, Polygon) else union.geoms
    for poly in polys:
        if poly.is_empty or not poly.is_valid:
            continue
        x, y = poly.exterior.xy
        dwg.add(dwg.polyline(list(zip(x, y)), stroke="black", fill="none", stroke_width=0.3))
    dwg.save()

    print(f"✅ SVG généré : {SVG_OUT_DIR / f'{name}.svg'}")
