# config.py
from pathlib import Path

# 📁 Chemins globaux
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/home/moi/Documents/EmportePieceData")  # dossier externe

DEBUG_DIR = DATA_DIR / "debug_out"
IMG_IN_DIR = DATA_DIR / "images"
SVG_OUT_DIR = DATA_DIR / "svg_out"
SVG_IN_DIR = DATA_DIR / "svg_in"
STL_OUT_DIR = DATA_DIR / "stl_out"
