# app.py
import os
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, Response, abort
from flask_cors import CORS

from config import CACHE_TTL, DEMO_MODE, BBOX, REGION_NAME
from fetchers.cache import fetch_with_fallback, read_cache
from fetchers.rainfall_power import fetch_power_rainfall
from fetchers.rainfall_openmeteo import fetch_openmeteo_rainfall
from engine.risk_engine import compute_risk_zones

# GPM is optional. If earthaccess / netCDF4 aren't installed, the app
# still runs with POWER + Open-Meteo as the fallback chain.
try:
    from fetchers.rainfall_gpm import fetch_gpm_rainfall
    GPM_AVAILABLE = True
except Exception as e:
    print(f"[warn] GPM fetcher unavailable, using POWER/Open-Meteo only: {e}")
    GPM_AVAILABLE = False
    fetch_gpm_rainfall = None

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

_last_updated = {"ts": None, "source": None, "stale": True}


def get_rainfall(days_back=7):
    cache_key = f"rainfall_{days_back}d"

    if DEMO_MODE:
        cached, _ = read_cache(cache_key, ttl_seconds=0)
        return {"data": cached or [], "source": "demo_cache", "stale": True, "error": None}

    if GPM_AVAILABLE:
        primary = fetch_gpm_rainfall
        fallbacks = [fetch_power_rainfall, fetch_openmeteo_rainfall]
    else:
        primary = fetch_power_rainfall
        fallbacks = [fetch_openmeteo_rainfall]

    return fetch_with_fallback(
        cache_key=cache_key,
        ttl=CACHE_TTL["gpm"],
        primary_fn=lambda: primary(days_back=days_back),
        fallback_fns=[lambda fn=fn: fn(days_back=days_back) for fn in fallbacks],
    )


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "region": REGION_NAME,
        "demo_mode": DEMO_MODE,
        "gpm_available": GPM_AVAILABLE,
    }


@app.get("/api/risk")
def get_risk():
    rainfall = get_rainfall(days_back=7)

    if not rainfall["data"]:
        return jsonify({
            "error": "No rainfall data available",
            "detail": rainfall["error"],
            "region": REGION_NAME,
        }), 503

    gj = compute_risk_zones(rainfall["data"])
    gj["metadata"]["source"] = rainfall["source"]
    gj["metadata"]["stale"] = rainfall["stale"]
    gj["metadata"]["error"] = rainfall["error"]
    gj["metadata"]["bbox"] = BBOX
    gj["metadata"]["gpm_available"] = GPM_AVAILABLE

    if not rainfall["stale"]:
        _last_updated["ts"] = datetime.now(timezone.utc).isoformat()
        _last_updated["source"] = rainfall["source"]
        _last_updated["stale"] = False

    return jsonify(gj)


@app.get("/api/last_updated")
def last_updated():
    return {**_last_updated, "region": REGION_NAME}


from alerts.telegram import process_alerts

@app.get("/api/alerts/check")
def check_alerts():
    # Allow query param ?lang=sw or ?lang=lg
    from flask import request
    lang = request.args.get("lang", "en")
    
    rainfall = get_rainfall(days_back=7)
    if not rainfall["data"]:
        return jsonify({"error": "No data to process"}), 503
        
    gj = compute_risk_zones(rainfall["data"])
    result = process_alerts(gj, lang=lang)
    return jsonify(result)

# GIBS Proxy route to avoid browser CORS / OpaqueResponseBlocking issues
GIBS_BASE = (
    "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
    "MODIS_Terra_CorrectedReflectance_TrueColor/default"
)

@app.get("/api/gibs/<date>/<int:z>/<int:y>/<int:x>.jpg")
def gibs_proxy(date, z, y, x):
    upstream = f"{GIBS_BASE}/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
    try:
        r = requests.get(upstream, timeout=10)
    except requests.RequestException as e:
        abort(502, description=f"GIBS fetch failed: {e}")

    if r.status_code != 200:
        abort(r.status_code, description=f"GIBS returned {r.status_code}")

    resp = Response(r.content, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
