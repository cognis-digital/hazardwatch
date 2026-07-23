"""Keyless authoritative public-data feed adapters → normalized HazardEvents.

All sources are free and require no API key:
  * USGS Earthquakes  (real-time GeoJSON)         earthquake.usgs.gov
  * NASA EONET        (natural events: fires/storms/volcanoes)  eonet.gsfc.nasa.gov
  * NWS/NOAA Alerts   (active US weather alerts, GeoJSON)       api.weather.gov

Each parser takes already-decoded JSON and returns list[HazardEvent]. `SOURCES`
maps a source name → its live URL + parser for the `refresh` pipeline.
"""

from __future__ import annotations

from .event import HazardEvent, clamp, parse_iso

# ---- USGS earthquakes -----------------------------------------------------
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"


def parse_usgs(data) -> list:
    out = []
    for f in data.get("features", []):
        p = f.get("properties", {}) or {}
        g = (f.get("geometry") or {}).get("coordinates") or [0, 0]
        mag = p.get("mag") or 0.0
        out.append(HazardEvent(
            id=f"usgs:{f.get('id')}", source="usgs", kind="earthquake",
            title=p.get("place") or "earthquake", ts=(p.get("time") or 0) / 1000.0,
            lat=float(g[1]), lon=float(g[0]),
            severity=round(clamp(float(mag), 0.0, 10.0), 2),
            url=p.get("url") or "", raw_severity=f"M{mag}"))
    return out


# ---- NASA EONET -----------------------------------------------------------
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=200"
_EONET_KIND = {"wildfires": "wildfire", "severe storms": "storm", "volcanoes": "volcano",
               "floods": "flood", "sea and lake ice": "ice", "drought": "drought",
               "dust and haze": "dust", "earthquakes": "earthquake", "landslides": "landslide",
               "snow": "snow", "temperature extremes": "heat", "water color": "water"}
_EONET_SEV = {"wildfire": 6.0, "storm": 6.0, "volcano": 7.0, "flood": 6.0, "landslide": 6.0}


def parse_eonet(data) -> list:
    out = []
    for e in data.get("events", []):
        cats = e.get("categories") or [{}]
        cat = (cats[0].get("title") or "other").lower()
        kind = _EONET_KIND.get(cat, "other")
        geoms = e.get("geometry") or []
        if not geoms:
            continue
        g = geoms[-1]  # latest observation
        coords = g.get("coordinates") or [0, 0]
        lon, lat = _point(coords)
        out.append(HazardEvent(
            id=f"eonet:{e.get('id')}", source="eonet", kind=kind,
            title=e.get("title") or kind, ts=parse_iso(g.get("date", "")),
            lat=lat, lon=lon, severity=_EONET_SEV.get(kind, 5.0),
            url=e.get("link") or "", raw_severity=cat))
    return out


def _point(coords):
    """Return (lon, lat) from a Point or the centroid of a Polygon ring."""
    if coords and isinstance(coords[0], (int, float)):
        return float(coords[0]), float(coords[1])
    # polygon: coords[0] is a ring of [lon,lat]
    try:
        ring = coords[0]
        lon = sum(p[0] for p in ring) / len(ring)
        lat = sum(p[1] for p in ring) / len(ring)
        return float(lon), float(lat)
    except Exception:
        return 0.0, 0.0


# ---- NWS / NOAA active alerts --------------------------------------------
NWS_URL = "https://api.weather.gov/alerts/active"
_NWS_SEV = {"extreme": 9.0, "severe": 7.0, "moderate": 5.0, "minor": 3.0, "unknown": 4.0}
_NWS_KIND = [("tornado", "tornado"), ("hurricane", "storm"), ("flood", "flood"),
             ("heat", "heat"), ("fire", "wildfire"), ("winter", "snow"), ("wind", "storm"),
             ("thunderstorm", "storm"), ("volcano", "volcano"), ("tsunami", "tsunami")]


def parse_nws(data) -> list:
    out = []
    for f in data.get("features", []):
        p = f.get("properties", {}) or {}
        ev = (p.get("event") or "alert")
        kind = next((k for token, k in _NWS_KIND if token in ev.lower()), "other")
        g = (f.get("geometry") or {})
        lon, lat = (0.0, 0.0)
        if g.get("type") == "Point":
            lon, lat = _point(g.get("coordinates") or [0, 0])
        elif g.get("coordinates"):
            lon, lat = _point(g["coordinates"])
        sev = _NWS_SEV.get((p.get("severity") or "unknown").lower(), 4.0)
        out.append(HazardEvent(
            id=f"nws:{p.get('id') or f.get('id')}", source="nws", kind=kind,
            title=p.get("headline") or ev, ts=parse_iso(p.get("sent", "")),
            lat=lat, lon=lon, severity=sev, url=p.get("web") or "",
            raw_severity=p.get("severity") or ""))
    return out


SOURCES = {
    "usgs": {"url": USGS_URL, "parse": parse_usgs, "desc": "USGS earthquakes (real-time)"},
    "eonet": {"url": EONET_URL, "parse": parse_eonet, "desc": "NASA EONET natural events"},
    "nws": {"url": NWS_URL, "parse": parse_nws, "desc": "NWS/NOAA active US alerts"},
}
