# alerts/telegram.py
import os
import requests
from config import DEMO_MODE
from alerts.messages import MESSAGES

def send_telegram_message(text: str):
    """Sends a text message via Telegram Bot API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[warn] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. Cannot send.")
        return False

    if DEMO_MODE:
        print("\n--- DEMO MODE: SIMULATED TELEGRAM SEND ---")
        print(text)
        print("-----------------------------------------\n")
        return True

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("  -> Telegram alert sent successfully.")
        return True
    except Exception as e:
        print(f"  -> Failed to send Telegram alert: {e}")
        return False


def process_alerts(geojson: dict, lang: str = "en"):
    """
    Scans a GeoJSON FeatureCollection for 'High' risk zones.
    Sends a Telegram message for the worst zone found.
    """
    if lang not in MESSAGES:
        lang = "en"
    
    msgs = MESSAGES[lang]
    features = geojson.get("features", [])
    
    # Find all High risk features
    high_zones = [f for f in features if f.get("properties", {}).get("grade") == "High"]
    
    if not high_zones:
        print("  -> Alert check: No High-risk zones found.")
        return {"status": "ok", "sent": False, "message": msgs["no_alert"]}

    # Sort by score descending to get the absolute worst zone
    high_zones.sort(key=lambda x: x["properties"].get("score", 0), reverse=True)
    worst = high_zones[0]["properties"]
    
    # Format the message
    reason = worst["reasons"][0] if worst.get("reasons") else "Heavy rainfall accumulation"
    
    text = msgs["title"] + "\n\n" + msgs["body"].format(
        region=geojson.get("metadata", {}).get("region", "Unknown"),
        lat=worst.get("center_lat", 0),
        lon=worst.get("center_lon", 0),
        r1=worst.get("rain_1d_mm", 0),
        r3=worst.get("rain_3d_mm", 0),
        r7=worst.get("rain_7d_mm", 0),
        reason=reason
    )
    
    print(f"  -> Found {len(high_zones)} High-risk zone(s). Sending alert for worst zone...")
    success = send_telegram_message(text)
    
    return {
        "status": "ok",
        "sent": success,
        "zone_count": len(high_zones),
        "worst_score": worst.get("score")
    }
