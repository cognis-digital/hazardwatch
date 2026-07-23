"""Hazardwatch benchmark — data-correctness on bundled real sample feeds.

Not an ML metric; the "harness" for a data tool is: does every feed parse and
normalize correctly, is the merge idempotent (so scheduled refreshes don't
duplicate), and is the GeoJSON valid. Deterministic, offline. Regenerates RESULTS.md.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hazardwatch import SAMPLES_DIR, geo, store  # noqa: E402
from hazardwatch.sources import parse_eonet, parse_nws, parse_usgs  # noqa: E402

FIXTURES = [("usgs_quakes.json", parse_usgs, "usgs", 2),
            ("nasa_eonet.json", parse_eonet, "eonet", 5),
            ("nws_alerts.json", parse_nws, "nws", 2)]


def evaluate():
    parsed = {}
    all_events = []
    sources_ok = 0
    for fn, parse, name, expect_min in FIXTURES:
        p = os.path.join(SAMPLES_DIR, fn)
        with open(p, encoding="utf-8") as f:
            evs = parse(json.load(f))
        parsed[name] = len(evs)
        if len(evs) >= expect_min:
            sources_ok += 1
        all_events += evs

    # every event georeferenced + normalized
    geo_ok = all(-90 <= e.lat <= 90 and -180 <= e.lon <= 180 and (e.lat, e.lon) != (0.0, 0.0)
                 and e.kind and e.id.startswith(e.source + ":") for e in all_events)

    # merge idempotent: merging the same events twice adds nothing
    merged, added1 = store.merge([], all_events)
    _, added2 = store.merge(merged, all_events)
    idempotent = (added1 == len(all_events)) and (added2 == 0)

    # geojson valid: one feature per event, coords in range
    fc = geo.to_geojson(merged)
    gj_ok = (fc["type"] == "FeatureCollection" and len(fc["features"]) == len(merged)
             and all(-180 <= f["geometry"]["coordinates"][0] <= 180
                     and -90 <= f["geometry"]["coordinates"][1] <= 90 for f in fc["features"]))

    return {"parsed_by_source": parsed, "parsed_total": len(all_events),
            "sources_ok": sources_ok, "all_georeferenced": geo_ok,
            "merge_idempotent": idempotent, "geojson_valid": gj_ok,
            "kinds": sorted({e.kind for e in all_events})}


def write_results(res, path="RESULTS.md"):
    lines = [
        "# Hazardwatch — benchmark results", "",
        "Data-correctness on bundled real sample feeds (USGS / NASA EONET / NWS). "
        "Regenerate with `python bench/run_all.py`. Offline & deterministic — validates "
        "parsing, normalization, idempotent merge, and GeoJSON output.", "",
        f"- Sources parsed OK: **{res['sources_ok']}/3**",
        f"- Events parsed: **{res['parsed_total']}** {res['parsed_by_source']}",
        f"- All events georeferenced & normalized: **{res['all_georeferenced']}**",
        f"- Merge idempotent (safe for scheduled refresh): **{res['merge_idempotent']}**",
        f"- GeoJSON valid: **{res['geojson_valid']}**",
        f"- Hazard kinds seen: {', '.join(res['kinds'])}",
        "",
    ]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    res = evaluate()
    write_results(res)
    print(json.dumps(res, indent=2))
