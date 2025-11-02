#!/usr/bin/env python3
# coding: utf-8
"""
Étape 3 : SVG (lissé) -> STL multi-niveaux
- 3 dilatations (OFFSETS_MM)
- Extrusion 1 mm par couche (LAYER_THICKNESS_MM)
- Empilement Z et fusion finale
- Config centralisée via config.py
"""

import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import svg2paths
from config import (
    SVG_SMOOTH_OUT, DATA_DIR,
    OFFSETS_MM, LAYER_THICKNESS_MM, SCALE_PX_TO_MM, JOIN_STYLE
)

STL_DIR = DATA_DIR / "stl_out"
STL_DIR.mkdir(parents=True, exist_ok=True)

def path_to_points(path, samples_per_seg=80):
    """Discrétise un path svgpathtools (gère Beziers) en une liste de points complexes."""
    pts = []
    for seg in path:
        ts = np.linspace(0.0, 1.0, samples_per_seg, endpoint=True)
        pts.extend([seg.point(t) for t in ts])
    # fermer proprement
    if pts and abs(pts[0] - pts[-1]) > 1e-6:
        pts.append(pts[0])
    return pts

def svg_to_base_geometry(svg_file):
    """Lit un SVG et retourne une géométrie Shapely (union de polygones) en millimètres."""
    paths, _ = svg2paths(str(svg_file))
    polys = []
    for p in paths:
        pts = path_to_points(p)
        if len(pts) < 3:
            continue
        # SVG: y vers le bas -> on remonte l'axe Y ; scale px->mm
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

def extrude_layers(base_geom):
    """Crée les couches extrudées (Z empilé) pour chaque offset et renvoie un mesh fusionné."""
    meshes = []
    z = 0.0
    for d in OFFSETS_MM:
        # dilatation mm -> déjà en mm, pas de conversion
        g = base_geom.buffer(d, join_style=JOIN_STYLE)
        if g.is_empty:
            z += LAYER_THICKNESS_MM
            continue

        geoms = [g] if isinstance(g, Polygon) else list(g.geoms)
        for poly in geoms:
            if not poly.is_valid or poly.is_empty:
                continue
            # trimesh sait extruder directement un shapely.Polygon en mm
            try:
                m = trimesh.creation.extrude_polygon(poly, LAYER_THICKNESS_MM)
            except Exception:
                # réparation au besoin
                m = trimesh.creation.extrude_polygon(poly.buffer(0), LAYER_THICKNESS_MM)
            if m is None:
                continue
            # positionner la couche à Z
            m.apply_translation((0, 0, z))
            meshes.append(m)
        z += LAYER_THICKNESS_MM

    if not meshes:
        return None
    return trimesh.util.concatenate(meshes)

# ---- Run ----
for svg_file in SVG_SMOOTH_OUT.glob("*.svg"):
    name = svg_file.stem
    print(f"➡️ STL multi-niveaux : {name}")

    base = svg_to_base_geometry(svg_file)
    if base is None or base.is_empty:
        print(f"⚠️ Aucun contour valide pour {name}")
        continue

    mesh = extrude_layers(base)
    if mesh is None:
        print(f"⚠️ Échec extrusion : {name}")
        continue

    out_path = STL_DIR / f"{name}.stl"
    mesh.export(out_path)   # binaire par défaut
    print(f"✅ STL généré : {out_path}")
