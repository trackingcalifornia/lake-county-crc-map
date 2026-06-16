"""
build_map.py — generate docs/index.html from sites.csv
Usage: python3 build_map.py
No dependencies beyond Python stdlib.
"""

import base64
import csv
import json
import os
import re

SVC_LABELS = {
    "cooling":  '<span class="tag svc">&#10052; Cooling center</span>',
    "warming":  '<span class="tag svc">&#9832; Warming center</span>',
    "overnight":'<span class="tag svc">&#127769; Overnight capable</span>',
}
PWR_LABELS = {
    "generator": '<span class="tag pwr">&#128268; Generator</span>',
    "solar":     '<span class="tag pwr">&#9728; Solar backup</span>',
    "battery":   '<span class="tag pwr">&#128267; Device charging</span>',
}


def phone_digits(p):
    return re.sub(r"[^\d]", "", p)


def build_popup(row):
    name = row["name"].strip()
    address = row["address"].strip()
    status = row["status"].strip()
    phone = row["phone"].strip()
    website = row["website"].strip()
    services = [s.strip() for s in row["services"].split("|") if s.strip()]
    power = [s.strip() for s in row["power"].split("|") if s.strip()]
    pets = row["pets"].strip()
    capacity = row["capacity"].strip()
    notes = row["notes"].strip()
    feeding = row.get("feeding", "").strip()
    road_access = row.get("road_access", "").strip()

    status_cls = "active" if status == "Active" else "setup"
    status_label = "Active Resilience Center" if status == "Active" else "In Setup — Not Yet Active"

    parts = []
    parts.append('<div class="popup-inner">')
    parts.append('<div class="popup-name">' + name + '</div>')
    parts.append('<div class="popup-status ' + status_cls + '">' + status_label + '</div>')
    parts.append('<div class="popup-addr">' + address + '</div>')

    contact_parts = []
    if phone:
        digits = phone_digits(phone)
        contact_parts.append('<a href="tel:' + digits + '" class="popup-link">&#128222;&nbsp;' + phone + '</a>')
    if website:
        contact_parts.append('<a href="' + website + '" target="_blank" class="popup-link">&#127760;&nbsp;Website&nbsp;&#8599;</a>')
    if contact_parts:
        parts.append('<div class="popup-contact">' + ' &nbsp; '.join(contact_parts) + '</div>')

    tags = []
    for s in services:
        if s in SVC_LABELS:
            tags.append(SVC_LABELS[s])
    for p in power:
        if p in PWR_LABELS:
            tags.append(PWR_LABELS[p])
    if pets:
        tags.append('<span class="tag pet">&#128062;&nbsp;' + pets + '</span>')
    if capacity:
        tags.append('<span class="tag cap">&#128101;&nbsp;Up to ' + capacity + ' people</span>')
    if tags:
        parts.append('<div class="popup-tags">' + "".join(tags) + '</div>')

    if notes:
        parts.append('<div class="popup-notes">' + notes + '</div>')

    if feeding:
        parts.append(
            '<div class="popup-section">'
            '<div class="popup-section-label">&#127860;&nbsp;Feeding capacity</div>'
            '<div class="popup-section-text">' + feeding + '</div>'
            '</div>'
        )

    if road_access:
        parts.append(
            '<div class="popup-section">'
            '<div class="popup-section-label">&#128663;&nbsp;Road access</div>'
            '<div class="popup-section-text">' + road_access + '</div>'
            '</div>'
        )

    parts.append('<div class="popup-avail">Hours and availability are confirmed at the time of each event. Check the center’s website or social media for current status.</div>')
    parts.append('</div>')

    return "".join(parts)


TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Lake County Community Resilience Centers</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body { height: 100%; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
    #map { width: 100%; height: 100vh; }

    /* Title panel */
    .map-title { background: white; padding: 12px 16px; border-radius: 4px;
                 box-shadow: 0 1px 5px rgba(0,0,0,0.3); width: 312px; box-sizing: border-box; }
    .map-title h1 { font-size: 17px; font-weight: 700; color: #1a1a1a;
                    line-height: 1.3; margin: 0; }
    .map-title .instructions { display: flex; align-items: flex-start; gap: 8px;
                    background: #eef4ff; border-left: 3px solid #2563eb;
                    border-radius: 4px; padding: 7px 9px; margin: 8px 0 0; }
    .map-title .instructions-icon { font-size: 15px; flex-shrink: 0; line-height: 1.4; }
    .map-title .instructions p { font-size: 13px; color: #1e3a6e; margin: 0; line-height: 1.5; }

    /* Site list panel */
    .site-list { background: white; border-radius: 4px;
                 box-shadow: 0 1px 5px rgba(0,0,0,0.3); width: 312px; overflow: hidden; }
    .site-list-header { font-size: 10px; font-weight: 700; color: #666;
                        padding: 7px 12px 5px; border-bottom: 1px solid #eee;
                        text-transform: uppercase; letter-spacing: 0.06em; }
    .site-list-inner { max-height: 260px; overflow-y: auto; }
    .site-list-item { display: flex; align-items: center; gap: 8px; padding: 7px 12px;
                      cursor: pointer; font-size: 12px; color: #1a1a1a;
                      border-bottom: 1px solid #f0f0f0; line-height: 1.3; }
    .site-list-item:hover { background: #f0f6ff; }
    .site-list-item:last-child { border-bottom: none; }
    .site-list-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

    /* Partnership panel */
    .partnership-panel { background: white; padding: 11px 16px 13px; border-radius: 4px;
                         box-shadow: 0 1px 5px rgba(0,0,0,0.3); max-width: 280px;
                         text-align: center; display: block; text-decoration: none; }
    .partnership-panel:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.35); }
    .partnership-label { font-size: 11px; color: #555; font-weight: 600;
                         margin-bottom: 9px; }
    .partnership-logos { display: flex; align-items: center; justify-content: center; gap: 14px; }
    .partnership-logos img { height: 48px; width: auto; }
    .partnership-btn { display: inline-block; margin-top: 10px; background: #2563eb; color: white;
                       font-size: 11px; font-weight: 600; padding: 5px 14px; border-radius: 12px;
                       letter-spacing: 0.02em; }

    /* Popups */
    .leaflet-popup-content { margin: 10px 14px; min-width: 240px; max-width: 300px; }
    .popup-inner { font-size: 13px; }
    .popup-name { font-size: 15px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
    .popup-status { display: inline-block; font-size: 11px; font-weight: 600;
                    padding: 2px 8px; border-radius: 10px; margin-bottom: 8px; }
    .popup-status.active { background: #d4f4dd; color: #1a6b2e; }
    .popup-status.setup  { background: #fde8cc; color: #8a4a00; }
    .popup-addr { font-size: 12px; color: #444; margin-bottom: 6px; }
    .popup-contact { margin-bottom: 8px; }
    .popup-link { font-size: 12px; color: #2563eb; text-decoration: none; }
    .popup-link:hover { text-decoration: underline; }
    .popup-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
    .tag { font-size: 11px; padding: 2px 7px; border-radius: 10px; }
    .tag.svc { background: #dbeafe; color: #1e40af; }
    .tag.pwr { background: #fef3c7; color: #92400e; }
    .tag.pet { background: #f0fdf4; color: #166534; }
    .tag.cap { background: #f3f4f6; color: #374151; }
    .popup-notes { font-size: 11px; color: #555; margin-bottom: 6px; line-height: 1.4; }
    .popup-section { margin-bottom: 6px; }
    .popup-section-label { font-size: 11px; font-weight: 600; color: #374151; margin-bottom: 2px; }
    .popup-section-text { font-size: 11px; color: #555; line-height: 1.4; }
    .popup-avail { font-size: 10px; color: #888; border-top: 1px solid #eee;
                   padding-top: 6px; margin-top: 6px; line-height: 1.4; font-style: italic; }

    /* Legend */
    .legend { background: white; padding: 10px 14px; border-radius: 4px;
              box-shadow: 0 1px 5px rgba(0,0,0,0.3); font-size: 12px; }
    .legend-title { font-weight: 700; margin-bottom: 6px; color: #1a1a1a; }
    .legend-item { display: flex; align-items: center; gap: 8px;
                   margin-bottom: 4px; color: #333; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  </style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([39.10, -122.82], 10);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
  subdomains: 'abcd',
  maxZoom: 20
}).addTo(map);

L.geoJSON(COUNTY_GEOJSON_HERE, {
  style: { color: '#555', weight: 2, dashArray: '6 4', fillOpacity: 0 }
}).addTo(map);

// Title control
var TitleControl = L.Control.extend({
  options: { position: 'topleft' },
  onAdd: function() {
    var div = L.DomUtil.create('div', 'map-title');
    div.innerHTML = '<img src="LOGO_DATA_URI_HERE" style="width:72px;height:auto;display:block;margin:0 auto 8px;">'
      + '<h1>Lake County Community Resilience Centers</h1>'
      + '<div class="instructions"><span class="instructions-icon">&#128205;</span><p>Click a marker to see center details. For current hours and availability, contact the center or visit their website.</p></div>';
    L.DomEvent.disableClickPropagation(div);
    return div;
  }
});
new TitleControl().addTo(map);

// Site list control
var SiteListControl = L.Control.extend({
  options: { position: 'topleft' },
  onAdd: function() {
    var div = L.DomUtil.create('div', 'site-list');
    div.innerHTML = '<div class="site-list-header">All Centers</div>'
      + '<div class="site-list-inner" id="site-list-inner"></div>';
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    return div;
  }
});
new SiteListControl().addTo(map);

// Partnership panel — top right
var PartnershipControl = L.Control.extend({
  options: { position: 'topright' },
  onAdd: function() {
    var a = L.DomUtil.create('a', 'partnership-panel');
    a.href = 'https://trackingcalifornia.org/projects/charm/roadmap#gsc.tab=0';
    a.target = '_blank';
    a.innerHTML = '<div class="partnership-label">In partnership with</div>'
      + '<div class="partnership-logos">'
      + '<img src="CHARM_LOGO_URI_HERE" alt="CHARM Lake County"/>'
      + '<img src="HEATWISE_LOGO_URI_HERE" alt="HEATwise"/>'
      + '</div>'
      + '<div class="partnership-btn">Learn more &#8599;</div>';
    L.DomEvent.disableClickPropagation(a);
    return a;
  }
});
new PartnershipControl().addTo(map);

// Legend control
var LegendControl = L.Control.extend({
  options: { position: 'bottomright' },
  onAdd: function() {
    var div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<div class="legend-title">Site Status</div>'
      + '<div class="legend-item"><div class="legend-dot" style="background:#27ae60;"></div> Active</div>'
      + '<div class="legend-item"><div class="legend-dot" style="background:#e67e22;"></div> In Setup</div>';
    return div;
  }
});
new LegendControl().addTo(map);

map.attributionControl.setPrefix(
  'Built and maintained by <a href="https://trackingcalifornia.org" target="_blank">Tracking California</a>'
  + ' in partnership with Lake County COAD'
);

function makeIcon(status) {
  var color = status === 'Active' ? '#27ae60' : '#e67e22';
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="38" viewBox="0 0 28 38">'
    + '<path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 24 14 24S28 24.5 28 14C28 6.27 21.73 0 14 0z" fill="' + color + '"/>'
    + '<circle cx="14" cy="14" r="6" fill="white"/>'
    + '</svg>';
  return L.divIcon({
    html: svg, className: '',
    iconSize: [28, 38], iconAnchor: [14, 38], popupAnchor: [0, -38]
  });
}

var SITES = SITES_DATA_HERE;
var markerMap = {};
SITES.forEach(function(s) {
  var m = L.marker([s.lat, s.lng], {icon: makeIcon(s.status)})
    .bindPopup(s.popup, {maxWidth: 320})
    .addTo(map);
  markerMap[s.name] = m;
});

// Populate site list
var listEl = document.getElementById('site-list-inner');
SITES.forEach(function(s) {
  var item = document.createElement('div');
  item.className = 'site-list-item';
  var color = s.status === 'Active' ? '#27ae60' : '#e67e22';
  item.innerHTML = '<div class="site-list-dot" style="background:' + color + ';"></div><span>' + s.name + '</span>';
  item.onclick = function() {
    var m = markerMap[s.name];
    if (m) { map.setView(m.getLatLng(), 13); m.openPopup(); }
  };
  listEl.appendChild(item);
});
</script>
</body>
</html>'''


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, "sites.csv")
    geojson_path = os.path.join(base, "docs", "lake-county.geojson")
    out_path = os.path.join(base, "docs", "index.html")

    sites = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            popup = build_popup(row)
            sites.append({
                "lat":    float(row["lat"]),
                "lng":    float(row["lng"]),
                "status": row["status"].strip(),
                "name":   row["name"].strip(),
                "popup":  popup,
            })

    with open(geojson_path, encoding="utf-8") as f:
        county_geojson = f.read().strip()

    # COAD logo
    logo_path = os.path.join(base, "docs", "lakecountycoad_logo.png")
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("ascii")
    logo_data_uri = "data:image/png;base64," + logo_b64

    # CHARM logo
    charm_path = os.path.join(base, "docs", "charm_logo.png")
    with open(charm_path, "rb") as f:
        charm_b64 = base64.b64encode(f.read()).decode("ascii")
    charm_data_uri = "data:image/png;base64," + charm_b64

    # HEATwise logo (SVG)
    hw_path = os.path.join(base, "docs", "heatwise_logo.svg")
    with open(hw_path, "rb") as f:
        hw_b64 = base64.b64encode(f.read()).decode("ascii")
    hw_data_uri = "data:image/svg+xml;base64," + hw_b64

    sites_json = json.dumps(sites, ensure_ascii=False)
    html = TEMPLATE.replace("SITES_DATA_HERE", sites_json)
    html = html.replace("COUNTY_GEOJSON_HERE", county_geojson)
    html = html.replace("LOGO_DATA_URI_HERE", logo_data_uri)
    html = html.replace("CHARM_LOGO_URI_HERE", charm_data_uri)
    html = html.replace("HEATWISE_LOGO_URI_HERE", hw_data_uri)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {out_path} ({os.path.getsize(out_path):,} bytes, {len(sites)} sites)")


if __name__ == "__main__":
    main()
