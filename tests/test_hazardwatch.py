import io
import json
import os
from contextlib import redirect_stdout

from hazardwatch import SAMPLES_DIR, cli, event, geo, store
from hazardwatch.event import HazardEvent, parse_iso
from hazardwatch.sources import SOURCES, parse_eonet, parse_nws, parse_usgs


def _sample(fn, parse):
    with open(os.path.join(SAMPLES_DIR, fn), encoding="utf-8") as f:
        return parse(json.load(f))


def test_parse_iso_variants():
    assert parse_iso("2026-07-22T00:00:00Z") > 0
    assert parse_iso("2026-07-22T09:40:00-05:00") > 0
    assert parse_iso("") == 0.0
    a = parse_iso("2026-07-22T00:00:00Z")
    b = parse_iso("2026-07-22T00:00:00+00:00")
    assert abs(a - b) < 1e-6


def test_usgs_parse():
    evs = _sample("usgs_quakes.json", parse_usgs)
    assert len(evs) >= 2
    e = evs[0]
    assert e.source == "usgs" and e.kind == "earthquake"
    assert e.id.startswith("usgs:")
    assert -90 <= e.lat <= 90 and -180 <= e.lon <= 180
    assert 0 <= e.severity <= 10


def test_eonet_parse_kinds():
    evs = _sample("nasa_eonet.json", parse_eonet)
    assert len(evs) >= 5
    assert all(e.source == "eonet" for e in evs)
    assert all(e.kind for e in evs)


def test_nws_parse_severity_mapping():
    evs = _sample("nws_alerts.json", parse_nws)
    assert len(evs) == 2
    kinds = {e.kind for e in evs}
    assert "tornado" in kinds and "heat" in kinds
    tor = next(e for e in evs if e.kind == "tornado")
    assert tor.severity >= 9  # Extreme


def test_polygon_centroid():
    from hazardwatch.sources import _point
    lon, lat = _point([[[0, 0], [0, 2], [2, 2], [2, 0]]])
    assert abs(lon - 1.0) < 1e-6 and abs(lat - 1.0) < 1e-6
    lon, lat = _point([10.0, 20.0])
    assert lon == 10.0 and lat == 20.0


def test_merge_idempotent_and_dedup():
    evs = _sample("usgs_quakes.json", parse_usgs)
    merged, added = store.merge([], evs)
    assert added == len(evs)
    merged2, added2 = store.merge(merged, evs)
    assert added2 == 0 and len(merged2) == len(merged)


def test_merge_refreshes_existing():
    e1 = HazardEvent("usgs:x", "usgs", "earthquake", "old", 1.0, 10, 10, 3.0)
    e2 = HazardEvent("usgs:x", "usgs", "earthquake", "new", 2.0, 10, 10, 5.0)
    merged, added = store.merge([e1], [e2])
    assert added == 0 and len(merged) == 1 and merged[0].severity == 5.0


def test_prune_by_age():
    now = 2_000_000_000.0   # realistic epoch so the old event still has ts > 0
    keep = HazardEvent("a:1", "a", "x", "t", now - 100, 0.1, 0.1, 1.0)
    drop = HazardEvent("a:2", "a", "x", "t", now - 100 * 86400, 0.1, 0.1, 1.0)
    out = store.prune([keep, drop], max_age_days=30, now_ts=now)
    assert keep in out and drop not in out


def test_store_roundtrip(tmp_path):
    evs = _sample("nasa_eonet.json", parse_eonet)
    p = str(tmp_path / "h.json")
    store.save(p, evs)
    loaded = store.load(p)
    assert len(loaded) == len(evs)
    assert loaded[0].id == store.sort_recent(evs)[0].id


def test_geojson_and_filter():
    evs = _sample("nws_alerts.json", parse_nws)
    fc = geo.to_geojson(evs)
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) == 2
    hot = geo.filter_events(evs, min_severity=8.0)
    assert all(e.severity >= 8 for e in hot)
    filt = geo.filter_events(evs, kinds=["tornado"])
    assert all(e.kind == "tornado" for e in filt)


def test_sources_registry():
    assert set(SOURCES) == {"usgs", "eonet", "nws"}
    for s in SOURCES.values():
        assert s["url"].startswith("https://") and callable(s["parse"])


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


def test_cli_demo_and_selfcheck():
    rc, out = _run(["demo"])
    assert rc == 0 and "total" in out
    rc, out = _run(["selfcheck"])
    assert rc == 0 and "PASS" in out


def test_cli_refresh_offline_and_query(tmp_path):
    # seed a dataset from samples via an offline "store", then query/map
    ds = str(tmp_path / "hz.json")
    evs = _sample("nasa_eonet.json", parse_eonet) + _sample("usgs_quakes.json", parse_usgs)
    store.save(ds, evs)
    rc, out = _run(["report", "--dataset", ds])
    assert rc == 0 and json.loads(out)["total"] == len(evs)
    rc, out = _run(["map", "--dataset", ds])
    assert rc == 0 and json.loads(out)["type"] == "FeatureCollection"
    rc, out = _run(["events", "--dataset", ds, "--min-severity", "0"])
    assert rc == 0


def test_bench_passes():
    from bench.run_all import evaluate
    r = evaluate()
    assert r["sources_ok"] == 3
    assert r["all_georeferenced"] and r["merge_idempotent"] and r["geojson_valid"]
