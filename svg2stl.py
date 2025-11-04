#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import svgwrite
from svgpathtools import svg2paths
from shapely.geometry import Polygon
import trimesh
from config import SVG_OUT_DIR, DEBUG_DIR, STL_OUT_DIR

# DPI = 96
# PX_PER_MM = DPI / 25.4
OFF1, OFF3, OFF5 = 1.0, 3.0, 5.0  # mm

DEBUG_DIR.mkdir(parents=True, exist_ok=True)
STL_OUT_DIR.mkdir(parents=True, exist_ok=True)

for svg_file in SVG_OUT_DIR.glob("*.svg"):
    print(f"➡️ {svg_file.name}")

    paths, _ = svg2paths(str(svg_file))
    if len(paths) != 1:
        print(f"⚠️ {svg_file.name}: attend 1 seul path, trouvé {len(paths)}")
        continue
    path = paths[0]

    # Path -> polygone fermé (échantillonnage fin)
    pts = [path.point(t) for t in np.linspace(0, 1, 600)]
    # Ajustement à 42mm max
    xmin = min(p.real for p in pts)
    xmax = max(p.real for p in pts)
    ymin = min(p.imag for p in pts)
    ymax = max(p.imag for p in pts)
    max_dim_px = max(xmax - xmin, ymax - ymin)
    scale = 42.0 / max_dim_px

    coords_mm = [(p.real * scale, -p.imag * scale) for p in pts]
    if coords_mm[0] != coords_mm[-1]:
        coords_mm.append(coords_mm[0])
    base = Polygon(coords_mm)  # maintenant en millimètres
 
    if base.is_empty:
        print("⚠️ Contour vide.")
        continue

    if not base.is_valid:
        print("⚠️ Contour invalide.")
        continue


    # Offsets
    b1 = base.buffer(OFF1)
    b3 = base.buffer(OFF3)
    b5 = base.buffer(OFF5)

    # --- SVG debug (path noir + 3 dilatations rouge/orange/vert)
    debug_svg = DEBUG_DIR / f"{svg_file.stem}_debug.svg"
    dwg = svgwrite.Drawing(str(debug_svg))
    for g, color in [(base, "black"), (b1, "red"), (b3, "orange"), (b5, "green")]:
        geoms = [g] if isinstance(g, Polygon) else list(g.geoms)
        for poly in geoms:
            x, y = poly.exterior.xy
            dwg.add(dwg.polyline(list(zip(x, y)), stroke=color, fill="none", stroke_width=0.4))
    dwg.save()
    print(f"🧩 SVG debug : {debug_svg}")

    # --- Extrusions -> STL (un seul solide)
    def extrude(geom, h, z=0.0):
        meshes = []
        geoms = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
        for poly in geoms:
            if poly.is_empty:
                continue
            try:
                m = trimesh.creation.extrude_polygon(poly, h)
            except Exception:
                m = trimesh.creation.extrude_polygon(poly.buffer(0), h)
            m.apply_translation((0, 0, z))
            meshes.append(m)
        return trimesh.util.concatenate(meshes) if meshes else None

    # Anneaux 2D non chevauchants
    ring5 = b5.difference(b3)   # 5mm - 3mm
    ring3 = b3.difference(b1)   # 3mm - 1mm
    ring1 = b1.difference(base) # 1mm - base (cavité)

    m5 = extrude(ring5, 1.0, z=0.0)  # 0→1 mm
    m3 = extrude(ring3, 3.0, z=0.0)  # 0→3 mm
    m1 = extrude(ring1, 20.0, z=0.0) # 0→20 mm

    parts = [m for m in (m5, m3, m1) if m is not None]
    if not parts:
        print("⚠️ Rien à extruder.")
        continue

    mesh = trimesh.util.concatenate(parts)
    out = STL_OUT_DIR / f"{svg_file.stem}.stl"
    mesh.export(out)
    print(f"✅ STL : {out}")
