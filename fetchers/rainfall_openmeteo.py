# fetchers/rainfall_openmeteo.py
"""
Fallback #2: Open-Meteo Archive API. Free, no API key needed.
Returns daily precipitation_sum for the BBOX centroid over the past N days.
A single point collapses to one grid cell in the risk engine,
which is fine for a last-resort fallback.
"""
import datetime as dt
import requests

from config import BBOX


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_openmeteo_rainfall(days_back: int = 7):
    b = BBOX
    lat = (b["min_lat"] + b["max_lat"]) / 2
    lon = (b["min_lon"] + b["max_lon"]) / 2

    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days_back - 1)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "UTC",
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    daily = payload.get("daily", {})
    times = daily.get("time", [])
    values = daily.get("precipitation_sum", [])
    if not times or len(times) != len(values):
        raise RuntimeError("Open-Meteo returned empty or mismatched arrays")

    rows = []
    for d, v in zip(times, values):
        if v is None:
            continue
        rows.append({
            "lat": round(lat, 2),
            "lon": round(lon, 2),
            "date": d,
            "rain_mm": round(float(v), 2),
        })
    if not rows:
        raise RuntimeError("Open-Meteo returned no valid precipitation values")
    return rows
