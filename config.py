from dotenv import load_dotenv
load_dotenv()

# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Region: Mt Elgon + Lake Victoria basin.
# Change these four values to retarget the whole pipeline.
# ------------------------------------------------------------
BBOX = {
    "min_lat": -1.5,
    "max_lat": 1.5,
    "min_lon": 33.0,
    "max_lon": 35.5,
}
REGION_NAME = "Mt Elgon - Lake Victoria Basin"

# ------------------------------------------------------------
# Risk-engine thresholds. Every number is explainable.
# Units: millimetres (mm) of rainfall.
# ------------------------------------------------------------
THRESHOLDS = {
    "rain_1d_high": 50.0,
    "rain_1d_medium": 25.0,
    "rain_3d_high": 100.0,
    "rain_3d_medium": 50.0,
    "rain_7d_high": 180.0,
    "rain_7d_medium": 90.0,
    "slope_high": 15.0,
    "slope_medium": 8.0,
}

# Grid cell edge length in degrees. 0.1 deg ~ 11 km at the equator.
GRID_SIZE_DEG = 0.1

# Cache TTLs in seconds.
CACHE_TTL = {
    "gpm": 6 * 3600,
    "power": 24 * 3600,
    "openmeteo": 24 * 3600,
    "firms": 3 * 3600,
}

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
