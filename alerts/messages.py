# alerts/messages.py

MESSAGES = {
    "en": {
        "title": "🚨 HIGH FLOOD/LANDSLIDE RISK ALERT 🚨",
        "body": (
            "Region: {region}\n"
            "Grid Center: {lat:.2f}, {lon:.2f}\n\n"
            "Rainfall:\n"
            "  24h: {r1} mm\n"
            "  3-day: {r3} mm\n"
            "  7-day: {r7} mm\n\n"
            "Primary reason:\n"
            "  {reason}"
        ),
        "no_alert": "No High-risk zones detected. System nominal."
    },
    "lg": {
        "title": "🚨 OKULABULA KU LWA KUBA ULUMBI 🚨",
        "body": (
            "Ekitundu: {region}\n"
            "Akabanga: {lat:.2f}, {lon:.2f}\n\n"
            "Enkuba:\n"
            "  Amasawa 24: {r1} mm\n"
            "  Ennaku 3: {r3} mm\n"
            "  Ennaku 7: {r7} mm\n\n"
            "Ensonga enkulu:\n"
            "  {reason}"
        ),
        "no_alert": "Tewali kabi akalabiddwa. Embeera ya bulijjo."
    },
    "sw": {
        "title": "🚨 TAHADHARI YA HATARI KUBWA 🚨",
        "body": (
            "Eneo: {region}\n"
            "Kituo: {lat:.2f}, {lon:.2f}\n\n"
            "Mvua:\n"
            "  Saa 24: {r1} mm\n"
            "  Siku 3: {r3} mm\n"
            "  Siku 7: {r7} mm\n\n"
            "Sababu kuu:\n"
            "  {reason}"
        ),
        "no_alert": "Hakuna maeneo ya hatari kubwa yaliyogundulika. Hali ni nzuri."
    }
}
