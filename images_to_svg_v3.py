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
from fitCurves import fitCurve

TOL = 15
TOL = 27
SEED_POINT = (20,20)
# DELTA = 5
EPSILON = 1
MAX_ERROR = 3  # tolérance du fit Bézier

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
    debug_svg = DEBUG_DIR / f"{img_path.stem}_overlay.svg"
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
    largest = cv2.approxPolyDP(largest, EPSILON, True)

    # mask = np.zeros_like(binary)
    # cv2.drawContours(mask, [largest], -1, 255, -1)

    # # cv2.drawContours(binary, [largest], -1, (0, 0, 255), 1)    
    # # cv2.imwrite(str(debug_path), mask)

    # kernel = np.ones((DELTA, DELTA), np.uint8)
    # mask = cv2.erode(mask, kernel)
    # mask = cv2.dilate(mask, kernel)

    # # cv2.imwrite(str(debug_path2), mask)

    # contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # if not contours:
    #     print(f"⚠️ Aucun contour trouvé pour {img_path}")
    #     continue
    # pts = contours[0].reshape(-1, 2)
    pts = largest.reshape(-1, 2)
    poly = Polygon(pts)
    x, y = poly.exterior.xy
    pointlist = list(zip(x, y))

    # poly = poly.simplify(0.5, preserve_topology=True)
    poly_smooth = poly.simplify(0.5, preserve_topology=True)
    x, y = poly_smooth.exterior.xy
    pointlist_smooth = list(zip(x, y))

    # Conversion vers Bézier avec fitCurves
    ptsfloat = np.array(largest.reshape(-1, 2), dtype=float)
    beziers = fitCurve(ptsfloat, MAX_ERROR)
    # Nettoyage des NaN dans beziers
    beziers = [seg for seg in beziers if not np.isnan(np.array(seg)).any()]

    path_data = ""
    for seg in beziers:
        p0, c1, c2, p3 = seg  # points du segment Bézier cubique
        if not path_data:
            path_data += f"M {p0[0]},{p0[1]} "
        path_data += f"C {c1[0]},{c1[1]} {c2[0]},{c2[1]} {p3[0]},{p3[1]} "
    path_data += "Z"  # fermer le chemin

    dwg = svgwrite.Drawing(str(debug_svg), size=(w, h))
    dwg.add(dwg.image(href=str(img_path), insert=(0, 0), size=(w, h)))
    dwg.add(dwg.polyline(pointlist, stroke="red", fill="none", stroke_width=1))
    dwg.add(dwg.polyline(pointlist_smooth, stroke="green", fill="none", stroke_width=0.4))
    dwg.add(dwg.path(d=path_data, stroke="blue", fill="none", stroke_width=0.4))
    dwg.save()

    dwg = svgwrite.Drawing(str(out_svg), profile="tiny")
    dwg.add(dwg.polyline(pointlist, stroke="black", fill="none", stroke_width=0.4))
    dwg.save()
    print(f"✅ SVG généré : {out_svg}")
