#!/usr/bin/env python3
# coding: utf-8
"""
Étape 2 : Lissage vectoriel de SVG existants (via svgpathtools)
- Corrige le rayon Arc (complex)
- Filtre les micro-arcs
- Produit un fichier debug avec chemin brut (rouge) et lissé (vert)
"""

import os
import glob
import numpy as np
from svgpathtools import svg2paths, wsvg, Path, Line, Arc
from cmath import phase

# 📁 Dossiers
INPUT_DIR = "svg_out"
OUTPUT_DIR = "svg_smooth_out"
DEBUG_DIR = "debug_postprocess"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# ⚙️ Paramètres
ARC_TOLERANCE = 1.5   # sensibilité pour détecter un arc (px)
MIN_SEGMENTS = 3       # segments mini pour considérer un arc
MIN_RADIUS = 0.5       # rayon mini (évite les micro-arcs parasites)
DEBUG = True

def circle_from_3pts(A, B, C):
    """Retourne (centre, rayon) du cercle passant par 3 points complexes"""
    A, B, C = np.array([A.real, A.imag]), np.array([B.real, B.imag]), np.array([C.real, C.imag])
    temp = B**2 - A**2
    temp2 = C**2 - A**2
    det = 2 * np.linalg.det([B - A, C - A])
    if abs(det) < 1e-6:
        raise ZeroDivisionError
    cx = (temp[0]*(C[1]-A[1]) - temp2[0]*(B[1]-A[1])) / det
    cy = (temp2[1]*(B[0]-A[0]) - temp[1]*(C[0]-A[0])) / det
    center = complex(cx + A[0], cy + A[1])
    radius = abs(A[0] - (cx + A[0]))
    return center, radius

def fit_arcs(points, tol=ARC_TOLERANCE):
    """Convertit une suite de points en segments + arcs"""
    if len(points) < MIN_SEGMENTS:
        return [Line(start=points[0], end=points[-1])]
    arcs = []
    i = 0
    while i < len(points) - 2:
        A, B, C = points[i], points[i+1], points[i+2]
        try:
            center, radius = circle_from_3pts(A, B, C)
        except ZeroDivisionError:
            arcs.append(Line(start=A, end=B))
            i += 1
            continue
        if radius < MIN_RADIUS:
            arcs.append(Line(start=A, end=B))
            i += 1
            continue
        if abs(abs(B - center) - radius) < tol:
            arc = Arc(start=A, radius=complex(radius, radius), rotation=0,
                      large_arc=False, sweep=True, end=C)
            arcs.append(arc)
            i += 2
        else:
            arcs.append(Line(start=A, end=B))
            i += 1
    arcs.append(Line(start=points[-2], end=points[-1]))
    return arcs

for path_file in glob.glob(os.path.join(INPUT_DIR, "*.svg")):
    name = os.path.splitext(os.path.basename(path_file))[0]
    print(f"➡️ Lissage : {name}")

    paths, attributes = svg2paths(path_file)
    new_paths = []

    for path in paths:
        pts = [seg.start for seg in path] + [path[-1].end]
        smoothed = fit_arcs(pts)
        new_paths.append(Path(*smoothed))

    # 1️⃣ Export SVG lissé
    out_file = os.path.join(OUTPUT_DIR, f"{name}_smooth.svg")
    wsvg(new_paths, filename=out_file)
    print(f"✅ SVG lissé enregistré : {out_file}")

    # 2️⃣ Génération du SVG debug (superposition)
    debug_file = os.path.join(DEBUG_DIR, f"{name}_debug.svg")
    wsvg(
        paths + new_paths,
        filename=debug_file,
        attributes=(
            [{'stroke': 'red', 'fill': 'none', 'stroke_width': 0.5}] * len(paths) +
            [{'stroke': 'green', 'fill': 'none', 'stroke_width': 0.8}] * len(new_paths)
        )
    )
    print(f"🧩 Fichier debug : {debug_file}")
