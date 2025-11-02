#!/usr/bin/env python3
# coding: utf-8
"""
Étape 2 : Post-traitement SVG (simplification + lissage Bézier)
Utilise fitCurves + config.py pour les chemins
"""

import os
import numpy as np
from svgpathtools import svg2paths, wsvg, Path, CubicBezier, Line
from fitCurves.fitCurves import fit_curve
from config import SVG_OUT_DIR, SVG_SMOOTH_OUT, DEBUG_POST, FIT_ERROR

# 📁 Dossiers
for d in [SVG_SMOOTH_OUT, DEBUG_POST]:
    d.mkdir(parents=True, exist_ok=True)

def to_points_list(path):
    pts = [seg.start for seg in path]
    if len(path) > 0:
        pts.append(path[-1].end)
    return pts

def fit_path(points, error=FIT_ERROR):
    """Retourne une liste de CubicBezier simplifiées à partir d’une polyline"""
    if len(points) < 4:
        return [Line(start=points[0], end=points[-1])]
    coords = np.array([[p.real, p.imag] for p in points])
    curves = fit_curve(coords, error)
    return [CubicBezier(*(complex(x, y) for x, y in c)) for c in curves]

for svg_file in SVG_OUT_DIR.glob("*.svg"):
    name = svg_file.stem
    print(f"➡️ Lissage Bézier : {name}")

    paths, _ = svg2paths(str(svg_file))
    smooth_paths = []
    for path in paths:
        pts = to_points_list(path)
        smooth_curves = fit_path(pts)
        smooth_paths.append(Path(*smooth_curves))

    # SVG final lissé
    out_file = SVG_SMOOTH_OUT / f"{name}_bezier.svg"
    wsvg(smooth_paths, filename=str(out_file))
    print(f"✅ SVG lissé : {out_file}")

    # SVG debug (rouge = brut, vert = lissé)
    debug_file = DEBUG_POST / f"{name}_debug.svg"
    wsvg(
        paths + smooth_paths,
        filename=str(debug_file),
        attributes=(
            [{'stroke': 'red', 'fill': 'none', 'stroke_width': 0.5}] * len(paths)
            + [{'stroke': 'green', 'fill': 'none', 'stroke_width': 0.8}] * len(smooth_paths)
        )
    )
    print(f"🧩 Debug : {debug_file}")
