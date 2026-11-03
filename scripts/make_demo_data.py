# scripts/make_demo_data.py
"""
Generates a synthetic GeoJSON file for offline demo mode.
Features a fake storm over Mt Elgon to ensure High risk zones appear.
"""
import json
import math
from pathlib import Path

def generate_demo():
    # Base grid around the Mt Elgon / Lake Victoria basin
    min_lat, max_lat = -1.5, 1.5
    min_lon, max_lon = 33.0, 35.5
    grid_size = 0.2
    
    features = []
    # Center of the fake storm (Mt Elgon area)
    storm_lat, storm_lon = 1.0, 34.5 
    
    for lat in [min_lat + i*grid_size for i in range(int((max_lat-min_lat)/grid_size))]:
        for lon in [min_lon + i*grid_size for i in range(int((max_lon-min_lon)/grid_size))]:
            # Calculate distance to fake storm center
            dist = math.sqrt((lat - storm_lat)**2 + (lon - storm_lon)**2)
            
            # Storm decays with distance
            if dist < 0.5:
                grade = "High"
                r1, r3, r7 = 65.0, 120.0, 190.0
                reasons = [
                    "Last 24h rainfall 65.0 mm >= heavy-rain threshold 50.0 mm",
                    "3-day total 120.0 mm >= soil-saturation threshold 100.0 mm",
                    "7-day total 190.0 mm >= basin-storage threshold 180.0 mm"
                ]
                score = 0.95
            elif dist < 1.2:
                grade = "Medium"
                r1, r3, r7 = 35.0, 60.0, 100.0
                reasons = ["Last 24h rainfall 35.0 mm is in the wet-day range", "3-day total 60.0 mm is elevated"]
                score = 0.55
            else:
                grade = "Low"
                r1, r3, r7 = 5.0, 15.0, 40.0
                reasons = ["Cumulative rainfall below medium thresholds; low risk"]
                score = 0.12
                
            half = grid_size / 2
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
                    "score": score,
                    "rain_1d_mm": r1,
                    "rain_3d_mm": r3,
                    "rain_7d_mm": r7,
                    "reasons": reasons,
                    "center_lat": lat,
                    "center_lon": lon
                }
            })
            
    out = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "region": "Mt Elgon - Lake Victoria Basin (DEMO)",
            "source": "offline_demo_data",
            "stale": False,
            "bbox": {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon}
        }
    }
    
    p = Path("static/demo/sample_risk.geojson")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))
    print(f"Wrote {p} with {len(features)} features.")

if __name__ == "__main__":
    generate_demo()
