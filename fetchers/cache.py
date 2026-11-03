# fetchers/cache.py
import json
import time
from pathlib import Path
from config import CACHE_DIR


def cache_path(key: str) -> Path:
    safe = key.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe}.json"


def read_cache(key: str, ttl_seconds: int):
    """
    Returns (data, is_fresh):
      - file missing             -> (None, False)
      - file exists but expired  -> (data, False)   # usable as fallback
      - file exists and fresh    -> (data, True)
    """
    p = cache_path(key)
    if not p.exists():
        return None, False
    try:
        payload = json.loads(p.read_text())
    except Exception:
        return None, False
    age = time.time() - payload.get("_cached_at", 0)
    return payload.get("data"), age < ttl_seconds


def write_cache(key: str, data):
    p = cache_path(key)
    p.write_text(json.dumps({"_cached_at": time.time(), "data": data},
                            indent=2, default=str))


def fetch_with_fallback(cache_key, ttl, primary_fn, fallback_fns=None):
    """
    1) cache fresh            -> return cache
    2) else try primary then fallbacks
    3) all fail & cache exists -> return stale cache, stale=True
    """
    cached, fresh = read_cache(cache_key, ttl)
    if fresh:
        return {"data": cached, "source": "cache_fresh",
                "stale": False, "error": None}

    last_err = None
    for fn in [primary_fn] + list(fallback_fns or []):
        try:
            data = fn()
            if data is not None:
                write_cache(cache_key, data)
                return {"data": data, "source": fn.__name__,
                        "stale": False, "error": None}
        except Exception as e:
            last_err = f"{fn.__name__}: {e}"

    if cached is not None:
        return {"data": cached, "source": "cache_stale",
                "stale": True, "error": last_err}
    return {"data": None, "source": "none",
            "stale": True, "error": last_err or "all_fetchers_failed"}
