# creation d'un environnement
python3 -m venv env

# for images_to_svg.py
python3 -m pip install pillow opencv-python shapely svgwrite

# for svg_postprocess.py
python3 -m pip install shapely trimesh numpy svgpathtools

# for svg_to_stl.py
python3 -m pip install mapbox-earcut
# python3 -m pip install numpy shapely trimesh svgpathtools
# python3 -m pip install pyglet


## Commandes utiles
# source .venv/bin/activate
# python3 -m pip list
# python3 -m pip 
# deactivate
# python3 images_to_svg.py
# python3 svg_postprocess.py