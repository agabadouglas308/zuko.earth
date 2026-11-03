// static/app.js -- Leaflet dashboard for the hazard monitor.

const BBOX = { min_lat: -1.5, max_lat: 1.5, min_lon: 33.0, max_lon: 35.5 };
const CENTER = [
  (BBOX.min_lat + BBOX.max_lat) / 2,
  (BBOX.min_lon + BBOX.max_lon) / 2,
];

const map = L.map("map").setView(CENTER, 7);

const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

function yesterdayUTC() {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

// FIXED: maxNativeZoom limits requests to GIBS' max level 9.
// maxZoom allows the user to zoom in further; Leaflet will upscale the level-9 tiles.
const gibs = L.tileLayer(
  "/api/gibs/" + yesterdayUTC() + "/{z}/{y}/{x}.jpg",
  {
    maxNativeZoom: 9,
    maxZoom: 18,
    opacity: 0.75,
    attribution: "NASA GIBS / MODIS (proxied)",
  }
);

const riskGroup = L.layerGroup().addTo(map);

L.control
  .layers(
    { OpenStreetMap: osm },
    { "NASA GIBS (MODIS Terra)": gibs, "Risk zones": riskGroup },
    { collapsed: false }
  )
  .addTo(map);

const GRADE_COLOR = { Low: "#22c55e", Medium: "#f59e0b", High: "#ef4444" };

function styleFeature(feature) {
  const g = feature.properties.grade;
  const c = GRADE_COLOR[g] || "#888";
  return { color: c, weight: 1, fillColor: c, fillOpacity: 0.35 };
}

function popupFor(feature) {
  const p = feature.properties;
  const reasonsHtml = (p.reasons || []).map((r) => `<div>&bull; ${r}</div>`).join("");
  return (
    `<strong>${p.grade} risk</strong> (score ${p.score})<br>` +
    `<small>1d: ${p.rain_1d_mm} mm | 3d: ${p.rain_3d_mm} mm | 7d: ${p.rain_7d_mm} mm</small>` +
    `<hr style="margin:4px 0">` +
    reasonsHtml
  );
}

let firstRender = true;

async function fetchRisk() {
  try {
    const res = await fetch("/api/risk", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return { gj: await res.json(), fromDemo: false };
  } catch (e) {
    console.warn("live API failed, trying demo file:", e);
    const res = await fetch("/static/demo/sample_risk.geojson", { cache: "no-store" });
    if (!res.ok) throw new Error("Both live API and demo file failed");
    return { gj: await res.json(), fromDemo: true };
  }
}

async function render() {
  try {
    const { gj, fromDemo } = await fetchRisk();
    riskGroup.clearLayers();
    const layer = L.geoJSON(gj, {
      style: styleFeature,
      onEachFeature: (f, l) => l.bindPopup(popupFor(f)),
    });
    layer.addTo(riskGroup);
    if (firstRender && layer.getBounds().isValid()) {
      map.fitBounds(layer.getBounds(), { padding: [20, 20] });
      firstRender = false;
    }
    updateSourceLabel(gj.metadata || {}, fromDemo);
  } catch (e) {
    console.error(e);
    document.getElementById("source").textContent = "ERROR: " + e.message;
  }
}

function updateSourceLabel(meta, fromDemo) {
  const src = fromDemo ? "demo/sample_risk.geojson" : meta.source || "unknown";
  const stale = fromDemo || meta.stale ? " (stale)" : "";
  document.getElementById("source").textContent = "source: " + src + stale;
}

async function updateLastUpdated() {
  try {
    const res = await fetch("/api/last_updated", { cache: "no-store" });
    if (!res.ok) return;
    const j = await res.json();
    if (j.ts) {
      document.getElementById("last-updated").textContent = "last updated: " + new Date(j.ts).toLocaleString();
    }
  } catch (e) {}
}

render();
updateLastUpdated();
setInterval(render, 60000);
setInterval(updateLastUpdated, 60000);

async function triggerAlerts() {
  const btn = document.getElementById("btn-check-alerts");
  const originalText = btn.textContent;
  btn.textContent = "Checking...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/alerts/check");
    const data = await res.json();
    
    if (data.sent) {
      btn.textContent = "Alert Sent!";
      btn.style.backgroundColor = "#22c55e";
    } else if (data.status === "ok" && !data.sent) {
      btn.textContent = "No High Risk";
      btn.style.backgroundColor = "#f59e0b";
    } else {
      btn.textContent = "Error";
      btn.style.backgroundColor = "#ef4444";
    }
  } catch (e) {
    console.error(e);
    btn.textContent = "Failed";
    btn.style.backgroundColor = "#ef4444";
  }

  // Revert button after 3 seconds
  setTimeout(() => {
    btn.textContent = originalText;
    btn.disabled = false;
    btn.style.backgroundColor = ""; // revert to CSS default
  }, 3000);
}

async function loadDemo() {
  try {
    const res = await fetch("/static/demo/sample_risk.geojson", { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const gj = await res.json();
    
    // Render the demo data directly, bypassing the API
    riskGroup.clearLayers();
    const layer = L.geoJSON(gj, {
      style: styleFeature,
      onEachFeature: (f, l) => l.bindPopup(popupFor(f)),
    });
    layer.addTo(riskGroup);
    map.fitBounds(layer.getBounds(), { padding: [20, 20] });
    
    document.getElementById("source").textContent = "source: OFFLINE DEMO DATA";
    document.getElementById("last-updated").textContent = "last updated: DEMO MODE";
  } catch (e) {
    console.error(e);
    alert("Failed to load demo data: " + e.message);
  }
}
