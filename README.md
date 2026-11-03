# Zuko.Earth | Elgon-Victoria Hazard Dashboard

A geospatial intelligence dashboard for monitoring flood and landslide risks in the Mt Elgon and Lake Victoria basin. Built for the NASA International Space Apps Challenge.

## 🚀 The Problem
The East African region around Mt Elgon is highly vulnerable to devastating floods and landslides. Early warning is critical, but local infrastructure often lacks reliable, real-time data ingestion. 

## 💡 Our Solution
We built a lightweight, highly resilient dashboard that ingests NASA Earth observation data, computes a transparent risk score, and displays it on a live map. It is designed to **degrade gracefully**—if NASA's primary servers go down or the internet is spotty, it falls back to secondary sources and cached data, ensuring first responders always have *something* to work with.

## ✨ Key Features
- **Live Geospatial Map:** Built with Leaflet.js and OpenStreetMap, overlaying NASA GIBS satellite imagery.
- **Transparent Risk Engine:** A rule-based scoring system (no black-box AI) that judges can easily audit.
- **3-Tier Data Fallback:** 
  1. NASA GPM IMERG (Primary, high resolution)
  2. NASA POWER (Fallback #1, no auth required)
  3. Open-Meteo Archive (Fallback #2, no API key required)
- **Smart Alerts:** Integrates with the Telegram Bot API to send alerts when a zone hits "High Risk".
- **Multi-Language Support:** Alert messages are pre-translated into **English**, **Luganda**, and **Swahili**.
- **Offline Demo Mode:** A built-in generator creates a synthetic "storm" over Mt Elgon so the dashboard can be demoed even if the conference Wi-Fi completely fails.

## 🧠 The Risk Engine (How it works)
We use a transparent, weighted rule-based model. For every 0.1° grid cell, we look at the 1-day, 3-day, and 7-day rainfall totals.

**The Formula:**
`Score = (0.5 × 1-Day Score) + (0.3 × 3-Day Score) + (0.2 × 7-Day Score)`

**The Thresholds (in `config.py`):**
- **1-Day:** > 50mm is High (Flash flood trigger), > 25mm is Medium
- **3-Day:** > 100mm is High (Soil saturation), > 50mm is Medium
- **7-Day:** > 180mm is High (Basin storage capacity), > 90mm is Medium

The weights prioritize immediate rainfall (1-day) because flash floods are the most acute danger in this region, while still accounting for antecedent soil moisture (3-day) and deep landslide triggers (7-day).

## 📡 Data Sources
- **NASA GPM IMERG:** High-resolution daily rainfall.
- **NASA POWER:** Solar and meteorological data (fallback rainfall).
- **Open-Meteo Archive:** Public, keyless fallback rainfall.
- **NASA GIBS:** MODIS Terra satellite imagery (True Color).
- **OpenStreetMap:** Base map tiles.

## 🛠️ Local Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/agabadouglas308/zuko.earth.git
   cd zuko.earth