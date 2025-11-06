from PIL import ImageFont, ImageDraw, Image
import cv2
import trimesh
from shapely.geometry import Polygon, MultiPolygon
import numpy as np

BORDER = 15
TEXT = "F8"

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


# 
# from shapely.geometry import Polygon, MultiPolygon
# import shapely.affinity as affinity

#L_10646.ttf
font = ImageFont.truetype("arial.ttf", 200)
img = Image.new("L", (800, 200), 0)
draw = ImageDraw.Draw(img)
draw.text((BORDER, BORDER), TEXT, fill=255, font=font)
img.save("debug_text.png")

arr = np.array(img)
contours, _ = cv2.findContours(arr, cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

x_min = y_min = float('inf')
x_max = y_max = float('-inf')

for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    x_min = min(x_min, x)
    y_min = min(y_min, y)
    x_max = max(x_max, x + w)
    y_max = max(y_max, y + h)

# parts = []
rect = Polygon([(x_min-BORDER,y_min), (x_min,y_min-BORDER),
                (x_max,y_min-BORDER), (x_max+BORDER,y_min),
                (x_max+BORDER,y_max), (x_max,y_max+BORDER),
                (x_min,y_max+BORDER), (x_min-BORDER,y_max)])
# mesh1 = extrude(rect,3.0)
# parts.append(mesh1)

for c in contours:
    pts = c.reshape(-1, 2)
    poly = Polygon(pts)
    rect = rect.difference(poly)

mesh = extrude(rect,3.0, z=3.0)
# mesh2 = extrude(rect,3.0, z=3.0)
# parts.append(mesh2)

# mesh = trimesh.util.concatenate(parts)
# # mesh = trimesh.creation.extrude_polygon(frame, height=3.0)
mesh.export("word_plate.stl")
