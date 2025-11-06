#!/usr/bin/env python3
# coding: utf-8
"""
svg2stl.py
- Lit des SVG (1 seul path attendu)
- Dilatations +1, +3, +5 mm
- Debug SVG des offsets
- STL unique composé de:
  * anneau (5mm-3mm) extrudé 1 mm  (z=0→1)
  * anneau (3mm-1mm) extrudé 3 mm  (z=1→4)
  * anneau (1mm-base) extrudé 20 mm (z=0→20)  => crée la cavité centrale (base) sur toute la hauteur
"""

import numpy as np
import svgwrite
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import svg2paths
from config import (
    SVG_OUT_DIR,           # Dossier d'entrée (tes SVG retouchés dans Inkscape)
    STL_OUT_DIR,           # Dossier de sortie STL
    DEBUG_DILATE_DIR,      # Dossier debug SVG
    SCALE_PX_TO_MM,        # px -> mm
    JOIN_STYLE             # 1=mitre, 2=round, 3=bevel
)

STL_OUT_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DILATE_DIR.mkdir(parents=True, exist_ok=True)

# --- paramètres offsets & hauteurs (mm)
OFF1, OFF3, OFF5 = 1.0, 3.0, 5.0
H_RING5, H_RING3, H_RING1 = 1.0, 3.0, 20.0  # hauteurs d'extrusion
Z_RING5, Z_RING3, Z_RING1 = 0.0, 1.0, 0.0   # positions en Z

def sample_path_to_polygon(path, step_mm=0.2):
    """Échantillonne un path svgpathtools en points (mm), puis Polygon Shapely."""
    pts = []
    for seg in path:
        L = max(seg.length(error=1e-4), 1e-9)
        n = max(int(np.ceil(L / step_mm)), 2)
        for t in np.linspace(0.0, 1.0, n, endpoint=False):
            z = seg.point(t)
            pts.append((z.real * SCALE_PX_TO_MM, -z.imag * SCALE_PX_TO_MM))
    # fermer
    z_end = path[-1].point(1.0)
    pts.append((z_end.real * SCALE_PX_TO_MM, -z_end.imag * SCALE_PX_TO_MM))
    poly = Polygon(pts)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if (poly.is_valid and not poly.is_empty) else None

def load_base_polygon(svg_file):
    """Charge le SVG, prend le plus grand path, renvoie un Polygon en mm."""
    paths, _ = svg2paths(str(svg_file))
    if not paths:
        return None
    # s'il y a plusieurs paths (au cas où), on prend celui à plus grande aire après sampling
    best = None
    best_area = -1.0
    for p in paths:
        poly = sample_path_to_polygon(p)
        if poly is None:
            continue
        area = poly.area
        if area > best_area:
            best, best_area = poly, area
    return best

def to_polylines(geom):
    """Retourne liste de boucles (x,y) pour Polygon/MultiPolygon."""
    if geom.is_empty:
        return []
    geoms = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    lines = []
    for g in geoms:
        x, y = g.exterior.xy
        lines.append(list(zip(x, y)))
        # On ignore les trous pour le debug (visuel plus clair)
    return lines

def save_debug_svg(name, base, b1, b3, b5):
    """SVG debug des offsets."""
    dwg = svgwrite.Drawing(str(DEBUG_DILATE_DIR / f"{name}_dilate.svg"))
    # base (noir)
    for loop in to_polylines(base):
        dwg.add(dwg.polyline(loop, stroke="#000000", fill="none", stroke_width=0.5))
    # +1mm (bleu)
    for loop in to_polylines(b1):
        dwg.add(dwg.polyline(loop, stroke="#0077ff", fill="none", stroke_width=0.5))
    # +3mm (vert)
    for loop in to_polylines(b3):
        dwg.add(dwg.polyline(loop, stroke="#00cc00", fill="none", stroke_width=0.5))
    # +5mm (rouge)
    for loop in to_polylines(b5):
        dwg.add(dwg.polyline(loop, stroke="#ff0000", fill="none", stroke_width=0.5))
    dwg.save()
    print(f"🧩 SVG debug : {DEBUG_DILATE_DIR / f'{name}_dilate.svg'}")

def extrude_geo(geom, height, z=0.0):
    """Extrude un Polygon/MultiPolygon Shapely (avec trous) en mesh trimesh."""
    meshes = []
    geoms = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    for g in geoms:
        if g.is_empty or not g.is_valid:
            continue
        try:
            m = trimesh.creation.extrude_polygon(g, height)
        except Exception:
            m = trimesh.creation.extrude_polygon(g.buffer(0), height)
        m.apply_translation((0, 0, z))
        meshes.append(m)
    return trimesh.util.concatenate(meshes) if meshes else None

# === MAIN ===
for svg_file in SVG_OUT_DIR.glob("*.svg"):
    name = svg_file.stem
    print(f"➡️ SVG→STL : {name}")

    base = load_base_polygon(svg_file)
    if base is None or base.is_empty:
        print("⚠️ Aucun path valide.")
        continue

    # Offsets (vectoriels, en mm)
    b1 = base.buffer(OFF1, join_style=JOIN_STYLE)
    b3 = base.buffer(OFF3, join_style=JOIN_STYLE)
    b5 = base.buffer(OFF5, join_style=JOIN_STYLE)

    # Debug des contours
    save_debug_svg(name, base, b1, b3, b5)

    # Anneaux 2D (pour éviter les volumes qui se chevauchent) :
    ring5 = b5.difference(b3)     # 5mm - 3mm
    ring3 = b3.difference(b1)     # 3mm - 1mm
    ring1 = b1.difference(base)   # 1mm - base  => crée la cavité du "base" sur toute la hauteur

    # Extrusions
    m5 = extrude_geo(ring5, H_RING5, z=Z_RING5)  # 0→1mm
    m3 = extrude_geo(ring3, H_RING3, z=Z_RING3)  # 1→4mm
    m1 = extrude_geo(ring1, H_RING1, z=Z_RING1)  # 0→20mm (cavité centrale conservée)

    parts = [m for m in [m5, m3, m1] if m is not None]
    if not parts:
        print("⚠️ Rien à extruder.")
        continue

    mesh = trimesh.util.concatenate(parts)
    out = STL_OUT_DIR / f"{name}.stl"
    mesh.export(out)
    print(f"✅ STL : {out}")
