#!/usr/bin/env python3
# coding: utf-8
"""
Étape 1 : Conversion des images noir/blanc → SVG vectorisés (OpenCV + Shapely)
- Extraction fidèle des contours
- Paramétrage aligné avec ton workflow
- Option pour activer/désactiver le lissage par buffer
"""

import os
import glob
import cv2
import numpy as np
import svgwrite
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# 📁 Dossiers
INPUT_DIR = "images"
OUTPUT_DIR = "svg_out"
DEBUG_DIR = "debug_out"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# ⚙️ Paramètres validés
THRESHOLD = 222           # seuil de binarisation
MIN_AREA_PX = 530         # filtre de bruit (aire min)
USE_APPROX = True         # simplification douce OpenCV
APPROX_EPSILON = 1.7      # tolérance approxPolyDP (px)

USE_SMOOTH = False         # activer ou désactiver le lissage par buffer
SMOOTH_BUFFER = 3.5       # rayon de lissage (px) si activé

for path in glob.glob(os.path.join(INPUT_DIR, "*")):
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"➡️ Traitement : {name}")

    # 1️⃣ Lecture et binarisation
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"⚠️ Impossible de lire {path}")
        continue

    _, bw = cv2.threshold(img, THRESHOLD, 255, cv2.THRESH_BINARY_INV)

    # 2️⃣ Détection des contours externes
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

                # Lissage optionnel
                if USE_SMOOTH:
                    poly = poly.buffer(SMOOTH_BUFFER, join_style=2).buffer(-SMOOTH_BUFFER, join_style=2)

                if not poly.is_empty:
                    shapes.append(poly)
                    filtered_contours.append(c)

    if not shapes:
        print(f"⚠️ Aucun contour valide pour {name}")
        continue

    # 3️⃣ Union géométrique
    try:
        union = unary_union(shapes)
    except Exception as e:
        print(f"⚠️ Erreur d'union pour {name} : {e}")
        union = MultiPolygon(shapes)

    # 4️⃣ Image debug fidèle (contours retenus uniquement)
    debug_img = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(debug_img, filtered_contours, -1, (0, 0, 255), 1)
    cv2.imwrite(os.path.join(DEBUG_DIR, f"{name}_contours.png"), debug_img)

    # 5️⃣ Export SVG
    svg_path = os.path.join(OUTPUT_DIR, f"{name}.svg")
    dwg = svgwrite.Drawing(svg_path, profile="tiny")

    polys = [union] if isinstance(union, Polygon) else union.geoms
    for poly in polys:
        if poly.is_empty or not poly.is_valid:
            continue
        x, y = poly.exterior.xy
        dwg.add(dwg.polyline(list(zip(x, y)), stroke="black", fill="none", stroke_width=0.3))

    dwg.save()
    print(f"✅ SVG généré : {svg_path}")
