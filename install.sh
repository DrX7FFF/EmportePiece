# creation d'un environnement
python3 -m venv env

# for images_to_svg.py
python3 -m pip install pillow opencv-python shapely svgwrite

# for svg_postprocess.py
python3 -m pip install shapely trimesh numpy svgpathtools


## Commandes utiles
# source .venv/bin/activate
# python3 -m pip list
# python3 -m pip 
# deactivate
# python3 images_to_svg.py
# python3 svg_postprocess.py