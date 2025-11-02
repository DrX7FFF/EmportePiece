#!/usr/bin/env python3
# coding: utf-8
"""
SVG → STL multi-niveaux
→ calcul unique des dilatations
→ export STL + SVG debug
"""

import numpy as np
import trimesh
import svgwrite
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import svg2paths
from config import (
    SVG_SMOOTH_OUT, STL_OUT_DIR, DEBUG_DILATE_DIR,
    OFFSETS_MM, LAYER_THICKNESS_MM, SCALE_PX_TO_MM, JOIN_STYLE
)

STL_OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DILATE_DIR.mkdir(parents=True, exist_ok=True)


def path_to_points(path, samples_per_seg=80):
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


def compute_dilations(base_geom):
    """Retourne la liste des géométries dilatées selon OFFSETS_MM."""
    dilations = []
    for d in OFFSETS_MM:
        g = base_geom.buffer(d, join_style=JOIN_STYLE)
        if not g.is_empty:
            dilations.append((d, g))
    return dilations


def save_debug_svg(dilations, name):
    dwg = svgwrite.Drawing(str(DEBUG_DILATE_DIR / f"{name}_dilate.svg"), profile="tiny")
    colors = ["#000000", "#0077ff", "#00cc00", "#ff0000", "#ff00ff"]
    for i, (offset, geom) in enumerate(dilations):
        geoms = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
        for poly in geoms:
            x, y = poly.exterior.xy
            color = colors[i % len(colors)]
            dwg.add(dwg.polyline(list(zip(x, y)), stroke=color, fill="none", stroke_width=0.4))
    dwg.save()
    print(f"🧩 SVG debug : {DEBUG_DILATE_DIR / f'{name}_dilate.svg'}")


def extrude_layers(dilations):
    meshes = []
    z = 0.0
    for _, geom in dilations:
        geoms = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
        for poly in geoms:
            if not poly.is_valid or poly.is_empty:
                continue
            m = trimesh.creation.extrude_polygon(poly, LAYER_THICKNESS_MM)
            m.apply_translation((0, 0, z))
            meshes.append(m)
        z += LAYER_THICKNESS_MM
    return trimesh.util.concatenate(meshes) if meshes else None


# === MAIN ===
for svg_file in SVG_SMOOTH_OUT.glob("*.svg"):
    name = svg_file.stem
    print(f"➡️ STL : {name}")
    base = svg_to_geometry(svg_file)
    if base is None or base.is_empty:
        print(f"⚠️ Aucun contour valide")
        continue

    dilations = compute_dilations(base)
    save_debug_svg(dilations, name)

    mesh = extrude_layers(dilations)
    if mesh is None:
        print(f"⚠️ Échec extrusion")
        continue

    out = STL_OUT_DIR / f"{name}.stl"
    mesh.export(out)
    print(f"✅ {out}")
