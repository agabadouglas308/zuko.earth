# fetchers/rainfall_gpm.py
"""
Primary rainfall source: NASA GPM IMERG Final Run Daily (GPM_3IMERGDF).

Searches for granules over the configured BBOX and date range, downloads
them, then reads the netCDF with xarray, coarsens to GRID_SIZE_DEG, and
flattens to a list of {lat, lon, date, rain_mm} rows.

If the required packages aren't installed or the download fails, an
exception propagates to fetch_with_fallback() and the POWER / Open-Meteo
tiers take over.
"""
import datetime as dt
from pathlib import Path

import numpy as np
import xarray as xr
import earthaccess

from config import BBOX, GRID_SIZE_DEG


def fetch_gpm_rainfall(days_back: int = 7):
    b = BBOX
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days_back - 1)

    # earthaccess reads EARTHDATA_USERNAME / EARTHDATA_PASSWORD from env
    auth = earthaccess.login(strategy="environment")
    if not getattr(auth, "authenticated", False):
        raise RuntimeError("Earthdata auth failed; check EARTHDATA_USERNAME/PASSWORD in .env")

    results = earthaccess.search_data(
        short_name="GPM_3IMERGDF",
        bounding_box=(b["min_lon"], b["min_lat"], b["max_lon"], b["max_lat"]),
        temporal=(start.isoformat(), end.isoformat()),
        count=days_back,
    )
    if not results:
        raise RuntimeError("No GPM_3IMERGDF granules found for the requested bbox/dates")

    data_dir = Path("cache/gpm")
    data_dir.mkdir(parents=True, exist_ok=True)
    files = earthaccess.download(results, str(data_dir))
    if not files:
        raise RuntimeError("GPM download returned no files")

    rows = []
    for fp in files:
        ds = xr.open_dataset(fp)

        # IMERG daily product uses 'precipitation' (mm/day). Fall back to
        # any variable whose name contains 'precip' if that changes.
        var = "precipitation"
        if var not in ds:
            candidates = [v for v in ds.data_vars if "precip" in v.lower()]
            if not candidates:
                ds.close()
                continue
            var = candidates[0]

        da = ds[var]
        if "time" in da.dims and da.sizes["time"] == 1:
            da = da.isel(time=0)

        da = da.sel(
            lat=slice(b["min_lat"], b["max_lat"]),
            lon=slice(b["min_lon"], b["max_lon"]),
        )

        if da.sizes.get("lat", 0) > 1 and da.sizes.get("lon", 0) > 1:
            dlat = abs(float(da.lat.values[1] - da.lat.values[0]))
            dlon = abs(float(da.lon.values[1] - da.lon.values[0]))
            da = da.coarsen(
                lat=max(1, int(GRID_SIZE_DEG / dlat)),
                lon=max(1, int(GRID_SIZE_DEG / dlon)),
                boundary="trim",
            ).mean()

        date_str = str(ds.attrs.get("BeginDate", end.isoformat()))[:10]
        for lat in da.lat.values:
            for lon in da.lon.values:
                val = float(da.sel(lat=lat, lon=lon).values)
                if not np.isnan(val):
                    rows.append({
                        "lat": float(lat),
                        "lon": float(lon),
                        "date": date_str,
                        "rain_mm": round(val, 2),
                    })
        ds.close()

    if not rows:
        raise RuntimeError("GPM files downloaded but no valid grid cells extracted")
    return rows
