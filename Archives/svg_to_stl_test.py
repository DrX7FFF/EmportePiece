#!/usr/bin/env python3
# coding: utf-8
"""
Test simple : SVG → STL (extrusion directe de 20 mm)
Pas de dilatation, pas d'empilement.
"""

import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import svg2paths
from config import SVG_SMOOTH_OUT, STL_OUT_DIR, SCALE_PX_TO_MM

STL_OUT_DIR.mkdir(parents=True, exist_ok=True)
EXTRUDE_HEIGHT_MM = 20.0


def path_to_points(path, samples_per_seg=100):
    pts = []
    for seg in path:
        ts = np.linspace(0.0, 1.0, samples_per_seg, endpoint=True)
        pts.extend([seg.point(t) for t in ts])
    if pts and abs(pts[0] - pts[-1]) > 1e-6:
        pts.append(pts[0])
    return pts


def svg_to_geometry(svg_file):
    paths, _ = svg2paths(str(svg_file))
    polys = []
    for p in paths:
        pts = path_to_points(p)
        if len(pts) < 3:
            continue
        coords = [(z.real * SCALE_PX_TO_MM, -z.imag * SCALE_PX_TO_MM) for z in pts]
        poly = Polygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_valid and not poly.is_empty:
            polys.append(poly)
    if not polys:
        return None
    try:
        return unary_union(polys)
    except Exception:
        return MultiPolygon(polys)


for svg_file in SVG_SMOOTH_OUT.glob("*.svg"):
    name = svg_file.stem
    print(f"➡️ Test extrusion : {name}")
    base = svg_to_geometry(svg_file)
    if base is None or base.is_empty:
        print(f"⚠️ Aucun contour valide")
        continue

    geoms = [base] if isinstance(base, Polygon) else list(base.geoms)
    meshes = []
    for poly in geoms:
        try:
            mesh = trimesh.creation.extrude_polygon(poly, EXTRUDE_HEIGHT_MM)
            meshes.append(mesh)
        except Exception as e:
            print(f"❌ Erreur extrusion : {e}")

    if not meshes:
        continue

    combined = trimesh.util.concatenate(meshes)
    out = STL_OUT_DIR / f"{name}_test.stl"
    combined.export(out)
    print(f"✅ STL généré : {out}")
