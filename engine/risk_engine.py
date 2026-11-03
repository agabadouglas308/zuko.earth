# engine/risk_engine.py
"""
Transparent rule-based risk scoring.

For each grid cell, take 1-day / 3-day / 7-day rainfall totals and score
each against config.THRESHOLDS. Combine with fixed weights into a 0-1
score, then bucket into Low / Medium / High.

Weights: 0.5*1d + 0.3*3d + 0.2*7d
  - 1d dominates: recent rain drives flash floods
  - 3d captures antecedent soil saturation
  - 7d captures basin storage / deep-landslide trigger
"""
from collections import defaultdict

from config import THRESHOLDS, GRID_SIZE_DEG, REGION_NAME


def _grade(score):
    if score >= 0.67:
        return "High"
    if score >= 0.34:
        return "Medium"
    return "Low"


def _score(total_mm, medium_mm, high_mm):
    """Piecewise-linear 0-1 score for a rainfall total."""
    if total_mm <= 0:
        return 0.0
    if total_mm >= high_mm:
        return 1.0
    if total_mm >= medium_mm:
        return 0.5 + 0.5 * (total_mm - medium_mm) / (high_mm - medium_mm)
    return 0.5 * total_mm / medium_mm


def compute_risk_zones(rainfall_rows):
    """rainfall_rows: list of {lat, lon, date, rain_mm}."""
    if not rainfall_rows:
        return {
            "type": "FeatureCollection",
            "features": [],
            "metadata": {"reason": "no rainfall data", "region": REGION_NAME},
        }

    # Group rows into grid cells keyed by lat/lon rounded to GRID_SIZE_DEG.
    grid = defaultdict(lambda: {"dates": {}})
    for row in rainfall_rows:
        key = (
            round(row["lat"] / GRID_SIZE_DEG) * GRID_SIZE_DEG,
            round(row["lon"] / GRID_SIZE_DEG) * GRID_SIZE_DEG,
        )
        grid[key]["dates"][row["date"]] = row["rain_mm"]

    features = []
    for (lat, lon), cell in grid.items():
        ds = sorted(cell["dates"].keys(), reverse=True)
        r1 = cell["dates"].get(ds[0], 0.0) if ds else 0.0
        r3 = sum(cell["dates"].get(d, 0.0) for d in ds[:3])
        r7 = sum(cell["dates"].get(d, 0.0) for d in ds[:7])

        s1 = _score(r1, THRESHOLDS["rain_1d_medium"], THRESHOLDS["rain_1d_high"])
        s3 = _score(r3, THRESHOLDS["rain_3d_medium"], THRESHOLDS["rain_3d_high"])
        s7 = _score(r7, THRESHOLDS["rain_7d_medium"], THRESHOLDS["rain_7d_high"])

        score = 0.5 * s1 + 0.3 * s3 + 0.2 * s7
        grade = _grade(score)

        reasons = []
        if r1 >= THRESHOLDS["rain_1d_high"]:
            reasons.append(f"Last 24h rainfall {r1:.1f} mm >= heavy-rain threshold {THRESHOLDS['rain_1d_high']} mm")
        elif r1 >= THRESHOLDS["rain_1d_medium"]:
            reasons.append(f"Last 24h rainfall {r1:.1f} mm is in the wet-day range")
        if r3 >= THRESHOLDS["rain_3d_high"]:
            reasons.append(f"3-day total {r3:.1f} mm >= soil-saturation threshold {THRESHOLDS['rain_3d_high']} mm")
        elif r3 >= THRESHOLDS["rain_3d_medium"]:
            reasons.append(f"3-day total {r3:.1f} mm is elevated")
        if r7 >= THRESHOLDS["rain_7d_high"]:
            reasons.append(f"7-day total {r7:.1f} mm >= basin-storage threshold {THRESHOLDS['rain_7d_high']} mm")
        if not reasons:
            reasons.append("Cumulative rainfall below medium thresholds; low risk")

        half = GRID_SIZE_DEG / 2
        coords = [[
            [lon - half, lat - half],
            [lon + half, lat - half],
            [lon + half, lat + half],
            [lon - half, lat + half],
            [lon - half, lat - half],
        ]]

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": coords},
            "properties": {
                "grade": grade,
                "score": round(score, 3),
                "rain_1d_mm": round(r1, 1),
                "rain_3d_mm": round(r3, 1),
                "rain_7d_mm": round(r7, 1),
                "reasons": reasons,
                "center_lat": lat,
                "center_lon": lon,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "region": REGION_NAME,
            "grid_size_deg": GRID_SIZE_DEG,
            "thresholds": THRESHOLDS,
            "weighting": "0.5*1d + 0.3*3d + 0.2*7d",
        },
    }
