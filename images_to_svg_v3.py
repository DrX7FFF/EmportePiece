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

SVG_OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def clean_background(img, seed_point=(20, 20), tol=15, debug_path=None):
    """Supprime le fond clair avec tolérance."""
    h, w = img.shape[:2]
    mask = np.zeros((h+2, w+2), np.uint8)
    loDiff, upDiff = (tol, tol, tol), (tol, tol, tol)
    flood_img = img.copy()
    cv2.floodFill(flood_img, mask, seed_point, (255, 255, 255), loDiff, upDiff)

    gray = cv2.cvtColor(flood_img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # if debug_path:
    #     cv2.imwrite(str(debug_path), binary)


    return binary

def largest_contour(binary):
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(binary)
    cv2.drawContours(mask, [largest], -1, 255, -1)
    return mask

def apply_buffer(mask, delta=5):
    kernel = np.ones((delta, delta), np.uint8)
    eroded = cv2.erode(mask, kernel)
    dilated = cv2.dilate(eroded, kernel)
    return dilated

def mask_to_svg(mask, out_file):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"⚠️ Aucun contour trouvé pour {out_file.name}")
        return
    pts = contours[0].reshape(-1, 2)
    poly = Polygon(pts)
    # poly = poly.simplify(0.5, preserve_topology=True)
    poly = poly.simplify(0.8, preserve_topology=True)
    
    dwg = svgwrite.Drawing(str(out_file), profile="tiny")
    x, y = poly.exterior.xy
    dwg.add(dwg.polyline(list(zip(x, y)), stroke="black", fill="none", stroke_width=0.4))
    dwg.save()
    print(f"✅ SVG généré : {out_file}")

# === MAIN ===
for img_path in IMG_IN_DIR.glob("*.png"):
    print(f"➡️ Traitement : {img_path.name}")
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        print(f"⚠️ Impossible de lire {img_path}")
        continue

    debug_gray = DEBUG_DIR / f"{img_path.stem}_gray.png"
    binary = clean_background(img, seed_point=(20, 20), tol=15, debug_path=debug_gray)
    mask = largest_contour(binary)
    if mask is None:
        print(f"⚠️ Aucun contour principal détecté.")
        continue

    cleaned = apply_buffer(mask, delta=10)
    cv2.imwrite(str(debug_gray), cleaned)

    out_svg = SVG_OUT_DIR / f"{img_path.stem}.svg"
    mask_to_svg(cleaned, out_svg)
