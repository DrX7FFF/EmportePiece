#!/usr/bin/env python3
# coding: utf-8

import cv2
import numpy as np
# from shapely.geometry import Polygon
import svgwrite
from config import IMG_IN_DIR, SVG_OUT_DIR, DEBUG_DIR
from fitCurves import fitCurve
import base64

TOL = 15
SEED_POINT = (20,20)
DELTA = 5
MAX_ERROR = 3  # tolérance du fit Bézier

SVG_OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# === MAIN ===
for img_path in IMG_IN_DIR.glob("*"):
    print(f"➡️ Traitement : {img_path.name}")
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        print(f"⚠️ Impossible de lire {img_path}")
        continue

    debug_path = DEBUG_DIR / f"{img_path.stem}.png"
    out_svg = SVG_OUT_DIR / f"{img_path.stem}.svg"

    # Nettoyage du fond et création image binaire
    h, w = img.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(img, mask, SEED_POINT, (255, 255, 255), (TOL, TOL, TOL), (TOL, TOL, TOL))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Recherche contour principal sur image binaire
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ Pas de contour trouvé {img_path}")
        continue
    largest = max(contours, key=cv2.contourArea)

    # Repassage par un bitmap pour nettoyer les points solitaire -Delta px + Delta px
    mask = np.zeros_like(binary)
    cv2.drawContours(mask, [largest], -1, 255, -1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (DELTA, DELTA))
    mask = cv2.erode(mask, kernel)
    mask = cv2.dilate(mask, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ Aucun contour re-trouvé pour {img_path}")
        continue
    largest = contours[0]

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

    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    href = f"data:image/png;base64,{b64}"

    dwg = svgwrite.Drawing(str(out_svg), size=(w, h))
    dwg.add(dwg.image(href=href, insert=(0, 0), size=(w, h)))
    dwg.add(dwg.path(d=path_data, stroke="blue", fill="none", stroke_width=0.4))
    dwg.save()

    print(f"✅ SVG généré : {out_svg}")
