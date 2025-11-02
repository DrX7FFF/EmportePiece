#!/usr/bin/env python3
# coding: utf-8
"""
Étape 2 : Conversion des SVG vectorisés → STL 3D multi-niveaux.
- Lecture des chemins SVG
- 3 dilatations (1, 3, 5 mm)
- Extrusion verticale (1 mm par couche)
- Fusion en un seul modèle STL
"""

import os
import glob
import numpy as np
import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import svg2paths

# Réglages
INPUT_DIR = "svg_out"
OUTPUT_DIR = "stl_out"
OFFSETS_MM = [0, 1, 3, 5]    # original + dilatations
THICKNESS_MM = 1.0           # épaisseur par couche
DPI = 96                     # conversion mm → px

def mm_to_px(mm):
    return mm / 25.4 * DPI

os.makedirs(OUTPUT_DIR, exist_ok=True)

for svg_path in glob.glob(os.path.join(INPUT_DIR, "*.svg")):
    name = os.path.splitext(os.path.basename(svg_path))[0]
    print(f"➡️ STL : {name}")

    # 1️⃣ Charger les chemins du SVG
    paths, _ = svg2paths(svg_path)
    if not paths:
        print(f"⚠️ Aucun chemin détecté dans {svg_path}")
        continue

    # 2️⃣ Convertir en polygones Shapely
    polys = []
    for path in paths:
        points = [(seg.start.real, seg.start.imag) for seg in path]
        if len(points) > 2:
            polys.append(Polygon(points))
    if not polys:
        print(f"⚠️ Aucun contour valide pour {name}")
        continue

    base_geom = unary_union(polys)

    # 3️⃣ Créer volumes extrudés
    meshes = []
    z = 0.0
    for offset in OFFSETS_MM:
        geom = base_geom.buffer(mm_to_px(offset))
        if geom.is_empty:
            continue

        if isinstance(geom, Polygon):
            geom_list = [geom]
        else:
            geom_list = geom.geoms

        for poly in geom_list:
            x, y = poly.exterior.xy
            points2d = np.column_stack([x, y])
            path = trimesh.path.Path2D(
                entities=[trimesh.path.entities.Line(np.arange(len(points2d)))],
                vertices=points2d
            )
            solid = path.extrude(THICKNESS_MM)
            solid.apply_translation((0, 0, z))
            meshes.append(solid)
        z += THICKNESS_MM

    if not meshes:
        print(f"⚠️ Aucun mesh généré pour {name}")
        continue

    combined = trimesh.util.concatenate(meshes)
    out_path = os.path.join(OUTPUT_DIR, f"{name}.stl")
    combined.export(out_path)
    print(f"✅ STL généré : {out_path}")
