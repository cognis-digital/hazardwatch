"""Hazardwatch CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import DEFAULT_DATASET, SAMPLES_DIR, __version__
from . import geo as geomod, report as reportmod, store as storemod
from .client import Client
from .sources import SOURCES


def cmd_sources(args):
    for name, s in SOURCES.items():
        print(f"  {name:7} {s['desc']}")
        print(f"          {s['url']}")
    return 0


def cmd_refresh(args):
    client = Client(offline=args.offline, cache_dir=args.cache)
    existing = storemod.load(args.dataset)
    incoming, errors = [], {}
    which = args.sources.split(",") if args.sources else list(SOURCES)
    for name in which:
        src = SOURCES.get(name)
        if not src:
            continue
        try:
            data = client.get_json(src["url"])
            evs = src["parse"](data)
            incoming += evs
            print(f"  {name:7} +{len(evs)} events", file=sys.stderr)
        except Exception as exc:
            errors[name] = str(exc)
            print(f"  {name:7} FAILED: {exc}", file=sys.stderr)
    merged, added = storemod.merge(existing, incoming)
    merged = storemod.prune(merged, args.max_age_days, time.time())
    storemod.save(args.dataset, merged)
    print(json.dumps({"added": added, "total": len(merged),
                      "sources_ok": len(which) - len(errors),
                      "errors": errors, "dataset": args.dataset}, indent=2))
    return 0


def cmd_events(args):
    evs = storemod.load(args.dataset)
    evs = geomod.filter_events(evs, kinds=args.kind.split(",") if args.kind else None,
                               min_severity=args.min_severity,
                               sources=args.source.split(",") if args.source else None)
    for e in evs[:args.limit]:
        print(f"  [{e.severity:>4}] {e.kind:11} {e.source:5} {e.title[:56]}")
    print(f"  ({len(evs)} match; showing {min(len(evs), args.limit)})")
    return 0


def cmd_map(args):
    evs = storemod.load(args.dataset)
    bbox = tuple(float(x) for x in args.bbox.split(",")) if args.bbox else None
    fc = geomod.to_geojson(evs, kinds=args.kind.split(",") if args.kind else None,
                           min_severity=args.min_severity, bbox=bbox)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=1)
        print(f"[+] {len(fc['features'])} features -> {args.out}")
    else:
        print(json.dumps(fc, indent=1))
    return 0


def cmd_report(args):
    print(json.dumps(reportmod.summarize(storemod.load(args.dataset)), indent=2))
    return 0


def _load_samples():
    from .sources import parse_usgs, parse_eonet, parse_nws
    out = []
    for fn, parse in (("usgs_quakes.json", parse_usgs), ("nasa_eonet.json", parse_eonet),
                      ("nws_alerts.json", parse_nws)):
        p = os.path.join(SAMPLES_DIR, fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out += parse(json.load(f))
    return out


def cmd_demo(args):
    evs = _load_samples()
    merged, _ = storemod.merge([], evs)
    print(f"Hazardwatch demo — parsed {len(evs)} events from bundled feeds (offline)")
    print(json.dumps(reportmod.summarize(merged), indent=2))
    return 0


def cmd_selfcheck(args):
    from bench.run_all import evaluate
    r = evaluate()
    ok = (r["parsed_total"] >= 8 and r["sources_ok"] == 3 and r["all_georeferenced"]
          and r["merge_idempotent"] and r["geojson_valid"])
    print(json.dumps(r, indent=2))
    print("SELFCHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="hazardwatch",
                                description="Self-updating public-safety hazard monitor from keyless open data — Cognis Digital")
    p.add_argument("--version", action="version", version=f"hazardwatch {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sc = sub.add_parser("sources", help="list the keyless data feeds")
    sc.set_defaults(func=cmd_sources)

    r = sub.add_parser("refresh", help="fetch latest events from all feeds, merge into the dataset")
    r.add_argument("--dataset", default=DEFAULT_DATASET)
    r.add_argument("--sources", help="comma list (default all)")
    r.add_argument("--max-age-days", type=float, default=30.0)
    r.add_argument("--offline", action="store_true")
    r.add_argument("--cache", default=".cache")
    r.set_defaults(func=cmd_refresh)

    e = sub.add_parser("events", help="query the dataset")
    e.add_argument("--dataset", default=DEFAULT_DATASET)
    e.add_argument("--kind"); e.add_argument("--source")
    e.add_argument("--min-severity", type=float, default=0.0)
    e.add_argument("--limit", type=int, default=25)
    e.set_defaults(func=cmd_events)

    m = sub.add_parser("map", help="emit GeoJSON of the dataset (filterable)")
    m.add_argument("--dataset", default=DEFAULT_DATASET)
    m.add_argument("--kind"); m.add_argument("--min-severity", type=float, default=0.0)
    m.add_argument("--bbox", help="W,S,E,N"); m.add_argument("--out")
    m.set_defaults(func=cmd_map)

    rp = sub.add_parser("report", help="summarize the dataset")
    rp.add_argument("--dataset", default=DEFAULT_DATASET); rp.set_defaults(func=cmd_report)

    dm = sub.add_parser("demo", help="parse the bundled sample feeds (offline) and summarize")
    dm.set_defaults(func=cmd_demo)

    sck = sub.add_parser("selfcheck", help="run the benchmark and assert it passes")
    sck.set_defaults(func=cmd_selfcheck)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
