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

# Matches what a Time-formatted Google Sheets cell exports as, e.g. "9:00am",
# "9:00:00 AM", "09:00", "16:30" -- seconds and am/pm are both optional so
# this tolerates whichever exact custom format ends up applied in the sheet.
HOUR_RE = re.compile(r"^(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)?$")


def parse_hour_label(raw):
    """Parse a sheet-normalized time string into a compact label like '9am'
    or '4:30pm'. Returns None if it doesn't match -- callers should fall back
    to showing the raw text rather than guessing at something unrecognized."""
    s = raw.strip().lower()
    if not s:
        return None
    if s == "noon":
        return "12pm"
    if s == "midnight":
        return "12am"
    m = HOUR_RE.match(s)
    if not m:
        return None
    hour, minute, _second, ampm = int(m.group(1)), m.group(2), m.group(3), m.group(4)
    if ampm:
        if not (1 <= hour <= 12):
            return None
        return str(hour) + (":" + minute if minute and minute != "00" else "") + ampm
    if minute is None:
        return None  # bare hour with no am/pm and no minutes is ambiguous
    if not (0 <= hour <= 23):
        return None
    h12 = hour % 12 or 12
    suffix = "am" if hour < 12 else "pm"
    return str(h12) + (":" + minute if minute != "00" else "") + suffix


def format_hours_range(opens_raw, closes_raw):
    """Return a display string like '9am–4pm' for the open-now banner, or
    None if there isn't enough usable info to show a range."""
    opens_raw, closes_raw = opens_raw.strip(), closes_raw.strip()
    if not opens_raw or not closes_raw:
        return None
    opens_label = parse_hour_label(opens_raw) or opens_raw
    closes_label = parse_hour_label(closes_raw) or closes_raw
    return opens_label + "–" + closes_label


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
    open_now = row.get("open_now", "").strip().lower() == "true"
    opens_at = row.get("opens_at", "").strip()
    closes_at = row.get("closes_at", "").strip()
    hours_label = format_hours_range(opens_at, closes_at) if open_now else None

    status_cls = "active" if status == "Active" else "setup"
    status_label = "Active Resilience Center" if status == "Active" else "In Setup — Not Yet Active"

    parts = []
    parts.append('<div class="popup-inner">')
    parts.append('<div class="popup-name">' + name + '</div>')
    parts.append('<div class="popup-status ' + status_cls + '">' + status_label + '</div>')
    if open_now:
        open_now_html = '&#128993;&nbsp;Open Now'
        if hours_label:
            open_now_html += ' &middot; ' + hours_label
        parts.append('<div class="popup-status open-now">' + open_now_html + '</div>')
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
    .open-now-toggle-row { display: flex; align-items: center; gap: 8px; padding: 11px 12px;
                          border-top: 1px solid #eee; font-size: 14px; font-weight: 700; color: #b45309; }
    .open-now-toggle-row label { display: flex; align-items: center; gap: 9px; cursor: pointer; }
    .open-now-toggle-row input[type="checkbox"] { cursor: pointer; width: 19px; height: 19px; flex-shrink: 0; }
    .open-now-empty { padding: 12px; font-size: 12px; color: #888; font-style: italic; text-align: center; }

    /* Partnership panel */
    .partnership-panel { background: white; padding: 11px 16px 13px; border-radius: 4px;
                         box-shadow: 0 1px 5px rgba(0,0,0,0.3); max-width: 280px;
                         text-align: center; display: block; text-decoration: none; }
    .partnership-panel:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.35); }
    .partnership-label { font-size: 11px; color: #555; font-weight: 600;
                         margin-bottom: 9px; }
    .partnership-logos { display: flex; align-items: center; justify-content: center; gap: 14px; }
    .partnership-logos img { height: 56px; width: auto; }
    .partnership-btn { display: inline-block; margin-top: 10px; background: #1a3460; color: white;
                       font-size: 11px; font-weight: 600; padding: 5px 14px; border-radius: 12px;
                       letter-spacing: 0.02em; }

    /* Popups */
    .leaflet-popup-content { margin: 10px 14px; min-width: 240px; max-width: 300px; }
    .popup-inner { font-size: 13px; }
    .popup-name { font-size: 15px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
    .popup-status { display: inline-block; font-size: 11px; font-weight: 600;
                    padding: 2px 8px; border-radius: 10px; margin-bottom: 8px; }
    .popup-status.active { background: #d4f4dd; color: #1a6b2e; }
    .popup-status.setup  { background: #e5e7eb; color: #4b5563; }
    .popup-status.open-now { background: #fef3c7; color: #b45309; margin-left: 6px; }
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

    /* ── Mobile bottom drawer ─────────────────────────────────────────── */
    #drawer-btn {
      display: none;
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 1001;
      background: #1a3460; color: white; border: none;
      padding: 14px 16px; padding-bottom: max(14px, env(safe-area-inset-bottom));
      font-size: 15px; font-weight: 600; letter-spacing: 0.02em;
      text-align: center; cursor: pointer;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.2);
    }
    #mobile-drawer {
      display: none;
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 1002;
      background: white; border-radius: 16px 16px 0 0;
      box-shadow: 0 -4px 20px rgba(0,0,0,0.25);
      max-height: 72vh; overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
      transform: translateY(100%);
      transition: transform 0.28s ease;
    }
    #mobile-drawer.open { transform: translateY(0); }
    .drawer-handle { width: 40px; height: 4px; background: #ddd; border-radius: 2px;
                     margin: 12px auto 8px; }
    .drawer-header { display: flex; justify-content: space-between; align-items: center;
                     padding: 0 16px 10px; }
    .drawer-title { font-size: 16px; font-weight: 700; color: #1a1a1a; }
    .drawer-close { background: none; border: none; font-size: 22px; cursor: pointer;
                    color: #666; padding: 4px; line-height: 1; }
    .drawer-instructions { background: #eef4ff; border-left: 3px solid #2563eb;
                           border-radius: 4px; padding: 10px 12px; margin: 0 16px 14px;
                           font-size: 13px; color: #1e3a6e; line-height: 1.5; }
    .drawer-list-header { font-size: 10px; font-weight: 700; color: #666;
                          padding: 0 16px 7px; text-transform: uppercase; letter-spacing: 0.06em; }
    .drawer-item { display: flex; align-items: center; gap: 10px;
                   padding: 13px 16px; cursor: pointer; font-size: 14px; color: #1a1a1a;
                   border-bottom: 1px solid #f0f0f0; }
    .drawer-item:active { background: #f0f6ff; }
    .drawer-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

    @media (max-width: 640px) {
      .site-list              { display: none !important; }
      .map-title .instructions { display: none; }
      .leaflet-top.leaflet-left { left: 16px; right: 16px; }
      .map-title              { width: 100%; text-align: center; }
      .partnership-panel      { padding: 7px 10px 8px; max-width: 160px; }
      .partnership-label      { display: none; }
      .partnership-logos img  { height: 36px; }
      .partnership-btn        { font-size: 10px; padding: 3px 10px; margin-top: 6px; }
      #drawer-btn             { display: block; }
      #mobile-drawer          { display: block; }

      /* Collapsed title when popup is open */
      .map-title.collapsed    { width: auto !important; padding: 5px 8px !important; }
      .map-title.collapsed h1 { display: none; }
      .map-title.collapsed img { width: 38px !important; margin: 0 auto !important; }
    }
  </style>
</head>
<body>
<div id="map"></div>
<button id="drawer-btn" onclick="openDrawer()">&#9776;&nbsp; All Centers &amp; Info</button>
<div id="mobile-drawer">
  <div class="drawer-handle"></div>
  <div class="drawer-header">
    <span class="drawer-title">Resilience Centers</span>
    <button class="drawer-close" onclick="closeDrawer()">&#10005;</button>
  </div>
  <div class="drawer-instructions">
    Tap a marker on the map to see center details. For the most up to date hours and availability, contact the center or visit their website.
  </div>
  <div class="drawer-list-header">All Centers</div>
  <div id="drawer-list"></div>
  <div class="open-now-toggle-row"><label><input type="checkbox" id="open-now-toggle-mobile"> Only show centers open now</label></div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([39.00, -122.72], 9);

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
      + '<div class="instructions"><span class="instructions-icon">&#128205;</span><p>Click a marker to see center details. For the most up to date hours and availability, contact the center or visit their website.</p></div>';
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
      + '<div class="site-list-inner" id="site-list-inner"></div>'
      + '<div class="open-now-toggle-row"><label><input type="checkbox" id="open-now-toggle"> Only show centers open now</label></div>';
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
      + '<div class="legend-item"><div class="legend-dot" style="background:#9e9e9e;"></div> In Setup</div>'
      + '<div class="legend-item"><div class="legend-dot" style="background:#27ae60;box-shadow:0 0 0 2px white, 0 0 0 6px #f59e0b;"></div> Open Now</div>';
    return div;
  }
});
new LegendControl().addTo(map);

map.attributionControl.setPrefix(
  'Built and maintained by <a href="https://trackingcalifornia.org" target="_blank">Tracking California</a>'
  + ' in partnership with Lake County COAD'
);

function makeIcon(status, openNow) {
  var color = status === 'Active' ? '#27ae60' : '#9e9e9e';
  var ring = openNow ? '<circle cx="14" cy="14" r="11.3" fill="none" stroke="#f59e0b" stroke-width="4.5"/>' : '';
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="38" viewBox="0 0 28 38">'
    + '<path d="M14 0C6.27 0 0 6.27 0 14c0 10.5 14 24 14 24S28 24.5 28 14C28 6.27 21.73 0 14 0z" fill="' + color + '"/>'
    + ring
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
  var m = L.marker([s.lat, s.lng], {icon: makeIcon(s.status, s.open_now)})
    .bindPopup(s.popup, {maxWidth: 320, autoPan: false})
    .addTo(map);
  markerMap[s.name] = m;
});

// Populate site list
var listEl = document.getElementById('site-list-inner');
SITES.forEach(function(s) {
  var item = document.createElement('div');
  item.className = 'site-list-item';
  item.dataset.openNow = s.open_now ? '1' : '0';
  var color = s.status === 'Active' ? '#27ae60' : '#9e9e9e';
  item.innerHTML = '<div class="site-list-dot" style="background:' + color + ';"></div><span>' + s.name + '</span>';
  item.onclick = function() {
    var m = markerMap[s.name];
    if (m) { map.setView(m.getLatLng(), 13); m.openPopup(); }
  };
  listEl.appendChild(item);
});

var openNowEmptyEl = document.createElement('div');
openNowEmptyEl.className = 'open-now-empty';
openNowEmptyEl.textContent = 'No centers currently activated.';
openNowEmptyEl.style.display = 'none';
listEl.appendChild(openNowEmptyEl);

// ── Open Now filter ─────────────────────────────────────────────────────────
function applyOpenNowFilter(onlyOpen) {
  var anyVisible = false;
  SITES.forEach(function(s) {
    var visible = !onlyOpen || s.open_now;
    if (visible) anyVisible = true;
    var m = markerMap[s.name];
    if (m) {
      if (visible && !map.hasLayer(m)) { m.addTo(map); }
      else if (!visible && map.hasLayer(m)) { map.removeLayer(m); }
    }
  });
  Array.prototype.forEach.call(listEl.querySelectorAll('.site-list-item'), function(item) {
    item.style.display = (!onlyOpen || item.dataset.openNow === '1') ? '' : 'none';
  });
  Array.prototype.forEach.call(drawerList.querySelectorAll('.drawer-item'), function(item) {
    item.style.display = (!onlyOpen || item.dataset.openNow === '1') ? '' : 'none';
  });
  openNowEmptyEl.style.display = (onlyOpen && !anyVisible) ? 'block' : 'none';
}

function onOpenNowToggle(e) {
  var checked = e.target.checked;
  document.getElementById('open-now-toggle').checked = checked;
  document.getElementById('open-now-toggle-mobile').checked = checked;
  applyOpenNowFilter(checked);
}
document.getElementById('open-now-toggle').addEventListener('change', onOpenNowToggle);
document.getElementById('open-now-toggle-mobile').addEventListener('change', onOpenNowToggle);

// ── Collapse title on mobile when popup opens ──────────────────────────────
map.on('popupopen', function(e) {
  if (window.innerWidth <= 640) {
    var t = document.querySelector('.map-title');
    if (t) t.classList.add('collapsed');
  }
  var markerPx   = map.latLngToContainerPoint(e.popup.getLatLng());
  var popupH     = e.popup._container ? e.popup._container.offsetHeight : 220;
  var popupCtrY  = markerPx.y - 38 - popupH / 2;
  var screenCtrY = map.getSize().y / 2;
  map.panBy([0, popupCtrY - screenCtrY], {animate: true, duration: 0.3});
});
map.on('popupclose', function() {
  var t = document.querySelector('.map-title');
  if (t) t.classList.remove('collapsed');
});

// ── Mobile drawer ──────────────────────────────────────────────────────────
function openDrawer()  { document.getElementById('mobile-drawer').classList.add('open'); }
function closeDrawer() { document.getElementById('mobile-drawer').classList.remove('open'); }

var drawerList = document.getElementById('drawer-list');
SITES.forEach(function(s) {
  var item = document.createElement('div');
  item.className = 'drawer-item';
  item.dataset.openNow = s.open_now ? '1' : '0';
  var color = s.status === 'Active' ? '#27ae60' : '#9e9e9e';
  item.innerHTML = '<div class="drawer-dot" style="background:' + color + ';"></div><span>' + s.name + '</span>';
  item.onclick = function() {
    closeDrawer();
    var m = markerMap[s.name];
    if (m) { map.setView(m.getLatLng(), 13); m.openPopup(); }
  };
  drawerList.appendChild(item);
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
                "lat":      float(row["lat"]),
                "lng":      float(row["lng"]),
                "status":   row["status"].strip(),
                "name":     row["name"].strip(),
                "popup":    popup,
                "open_now": row.get("open_now", "").strip().lower() == "true",
            })

    sites.sort(key=lambda s: s["name"].lower())

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
