# config.py
from pathlib import Path

# 📁 Chemins globaux
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/home/moi/Documents/EmportePieceData")  # dossier externe

IMAGES_DIR = DATA_DIR / "images"
SVG_OUT_DIR = DATA_DIR / "svg_out"
DEBUG_DIR = DATA_DIR / "debug_out"
SVG_SMOOTH_OUT = DATA_DIR / "svg_smooth_out"
DEBUG_POST = DATA_DIR / "debug_postprocess"

# ⚙️ Paramètres généraux
THRESHOLD = 222
MIN_AREA_PX = 530
USE_APPROX = True
APPROX_EPSILON = 1.7
USE_SMOOTH = True
SMOOTH_BUFFER = 3.5
FIT_ERROR = 2.5
