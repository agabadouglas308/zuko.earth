# fetchers/rainfall_power.py
"""
Fallback #1: NASA POWER daily precipitation (PRECTOTCORR).
Requests a single point at the BBOX centroid. Coarse resolution (~0.5 deg),
but the risk engine handles it — one point becomes one grid cell.
"""
import datetime as dt
import requests

from config import BBOX


POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_power_rainfall(days_back: int = 7):
    b = BBOX
    lat = (b["min_lat"] + b["max_lat"]) / 2
    lon = (b["min_lon"] + b["max_lon"]) / 2

    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days_back - 1)

    params = {
        "parameters": "PRECTOTCORR",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    r = requests.get(POWER_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    try:
        series = payload["properties"]["parameter"]["PRECTOTCORR"]
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Unexpected POWER response structure: {e}")

    rows = []
    for yyyymmdd, val in series.items():
        if val is None or val == -999:
            continue
        d = f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
        rows.append({
            "lat": round(lat, 2),
            "lon": round(lon, 2),
            "date": d,
            "rain_mm": round(float(val), 2),
        })
    if not rows:
        raise RuntimeError("POWER returned no valid PRECTOTCORR values")
    return rows
