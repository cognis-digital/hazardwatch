"""Offline example: parse the bundled feeds, merge, summarize, map."""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hazardwatch import SAMPLES_DIR, geo, report, store          # noqa: E402
from hazardwatch.sources import parse_eonet, parse_nws, parse_usgs  # noqa: E402

def main():
    evs = []
    for fn, parse in (("usgs_quakes.json", parse_usgs), ("nasa_eonet.json", parse_eonet),
                      ("nws_alerts.json", parse_nws)):
        with open(os.path.join(SAMPLES_DIR, fn), encoding="utf-8") as f:
            evs += parse(json.load(f))
    merged, added = store.merge([], evs)
    print(f"parsed+merged {added} events")
    print(json.dumps(report.summarize(merged), indent=2))
    print("geojson features:", len(geo.to_geojson(merged)["features"]))

if __name__ == "__main__":
    main()
