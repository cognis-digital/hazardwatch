# Hazardwatch — benchmark results

Data-correctness on bundled real sample feeds (USGS / NASA EONET / NWS). Regenerate with `python bench/run_all.py`. Offline & deterministic — validates parsing, normalization, idempotent merge, and GeoJSON output.

- Sources parsed OK: **3/3**
- Events parsed: **10** {'usgs': 2, 'eonet': 6, 'nws': 2}
- All events georeferenced & normalized: **True**
- Merge idempotent (safe for scheduled refresh): **True**
- GeoJSON valid: **True**
- Hazard kinds seen: earthquake, heat, storm, tornado, wildfire

