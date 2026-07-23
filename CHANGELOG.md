# Changelog

Adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-07-22

Initial release.

### Added
- **Keyless open-data adapters** (`sources.py`) — USGS earthquakes, NASA EONET
  (wildfires/storms/volcanoes/floods), NWS/NOAA active alerts → normalized `HazardEvent`
  (kind, time, lat/lon, 0–10 severity, agency URL).
- **Self-updating dataset** (`store.py`) — idempotent dedup-merge + rolling-window prune, so
  scheduled refreshes add recent events without duplicating.
- **Live refresh pipeline** (`client.py`, `cli.py refresh`) — fetch all feeds, merge, prune, save.
- **Query / map / report** — filter by kind/severity/bbox; GeoJSON output; summary.
- **Auto-update GitHub Action** (`.github/workflows/refresh.yml`) — 6-hour cron refreshes
  and commits `data/hazards.json` with no server. Reusable "static dataset → self-updating" pattern.
- **Verification harness** (`bench/run_all.py`) — data-correctness on bundled real sample
  feeds: parsing, normalization, idempotent merge, valid GeoJSON.
- CLI (`hazardwatch`): sources, refresh, events, map, report, demo, selfcheck.
- Ships an initial real dataset; 14 tests; CI across Python 3.9–3.13.
