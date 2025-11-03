#!/usr/bin/env python3
# coding: utf-8
"""
images_to_svg_v3.py
Nettoyage inspiré GIMP :
- flood fill fond
- inversion sélection
- garde la plus grande zone
- buffer -5 / +5 px
- sauvegarde du gray intermédiaire dans DEBUG_DIR
"""

import cv2
import numpy as np
from shapely.geometry import Polygon
import svgwrite
from config import IMG_IN_DIR, SVG_OUT_DIR, DEBUG_DIR

TOL = 15
SEED_POINT = (20,20)
DELTA = 5

SVG_OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


# === MAIN ===
for img_path in IMG_IN_DIR.glob("*.png"):
    print(f"➡️ Traitement : {img_path.name}")
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        print(f"⚠️ Impossible de lire {img_path}")
        continue

    debug_path = DEBUG_DIR / f"{img_path.stem}.png"
    debug_path2 = DEBUG_DIR / f"{img_path.stem}_fil.png"
    out_svg = SVG_OUT_DIR / f"{img_path.stem}.svg"

    # Nettoyage du fond et création image binaire
    h, w = img.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    flood_img = img.copy()
    cv2.floodFill(flood_img, mask, SEED_POINT, (255, 255, 255), (TOL, TOL, TOL), (TOL, TOL, TOL))
    gray = cv2.cvtColor(flood_img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Recherche contour principal sur image binaire
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ Pas de contour trouvé {img_path}")
        continue
    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(binary)
    cv2.drawContours(mask, [largest], -1, 255, -1)

    # cv2.drawContours(binary, [largest], -1, (0, 0, 255), 1)    
    # cv2.imwrite(str(debug_path), mask)

    kernel = np.ones((DELTA, DELTA), np.uint8)
    mask = cv2.erode(mask, kernel)
    mask = cv2.dilate(mask, kernel)

    # cv2.imwrite(str(debug_path2), mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ Aucun contour trouvé pour {img_path}")
        continue
    pts = contours[0].reshape(-1, 2)
    poly = Polygon(pts)
    # poly = poly.simplify(0.5, preserve_topology=True)
    poly = poly.simplify(0.8, preserve_topology=True)
    
    dwg = svgwrite.Drawing(str(out_svg), profile="tiny")
    x, y = poly.exterior.xy
    dwg.add(dwg.polyline(list(zip(x, y)), stroke="black", fill="none", stroke_width=0.4))
    dwg.save()
    print(f"✅ SVG généré : {out_svg}")
