"""Filter hazard events → GeoJSON FeatureCollection for maps."""

from __future__ import annotations


def filter_events(events, kinds=None, min_severity=0.0, bbox=None, sources=None):
    out = []
    for e in events:
        if kinds and e.kind not in kinds:
            continue
        if sources and e.source not in sources:
            continue
        if e.severity < min_severity:
            continue
        if bbox:
            w, s, ee, n = bbox
            if not (w <= e.lon <= ee and s <= e.lat <= n):
                continue
        out.append(e)
    return out


def to_geojson(events, **filters):
    evs = filter_events(events, **filters)
    feats = []
    for e in evs:
        feats.append({"type": "Feature",
                      "properties": {"id": e.id, "source": e.source, "kind": e.kind,
                                     "title": e.title, "severity": e.severity, "ts": e.ts,
                                     "url": e.url},
                      "geometry": {"type": "Point", "coordinates": [round(e.lon, 5),
                                                                    round(e.lat, 5)]}})
    return {"type": "FeatureCollection", "features": feats}
