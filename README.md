<h1 align="center">Hazardwatch</h1>
<p align="center"><i>A self-updating public-safety hazard monitor built on authoritative, keyless open data — earthquakes, wildfires, storms, volcanoes, and weather alerts, on one map.</i></p>
<p align="center">Part of the Cognis Neural Suite · <a href="https://cognis.digital">cognis.digital</a></p>

---

Hazardwatch pulls the latest events from **free, no-key US/global government feeds**, merges
them into one **normalized, deduplicated dataset**, and gives you query + GeoJSON map +
summary — **offline** on the saved data. A bundled **GitHub Action refreshes the dataset
every 6 hours with no server**, so the repo keeps itself current and *adds recent events
automatically*.

## Sources (all keyless, authoritative, public-domain)
| Source | What | Feed |
|---|---|---|
| **USGS** | Earthquakes (real-time) | earthquake.usgs.gov |
| **NASA EONET** | Wildfires · severe storms · volcanoes · floods | eonet.gsfc.nasa.gov |
| **NWS / NOAA** | Active US weather alerts | api.weather.gov |

Every source is normalized to one `HazardEvent` (kind, time, lat/lon, **0–10 severity**,
link back to the agency), so the map and queries are source-agnostic. Adding a feed is one
parser + one registry line.

## Quick start
```bash
python -m hazardwatch demo                       # parse bundled samples offline, summarize
python -m hazardwatch refresh                     # pull latest from all feeds → data/hazards.json
python -m hazardwatch report                      # counts by kind/source + most severe
python -m hazardwatch events --kind wildfire,earthquake --min-severity 5
python -m hazardwatch map --min-severity 6 --out hazards.geojson   # drop on any map
python -m hazardwatch selfcheck                   # data-correctness benchmark
```

## It updates itself
`.github/workflows/refresh.yml` runs `hazardwatch refresh` on a 6-hour cron, merges new
events (idempotent — no duplicates), prunes to a rolling 30-day window, and commits the
updated `data/hazards.json`. **No server, no key, no maintenance** — fork it and the dataset
stays live. That same pattern turns any static-dataset repo into a self-updating one.

## Verification
`python bench/run_all.py` validates parsing/normalization/idempotent-merge/GeoJSON against
bundled **real** sample feeds — offline and deterministic:

| Check | Result |
|---|---|
| Sources parsed OK | **3 / 3** |
| Events normalized & georeferenced | **✓** |
| Merge idempotent (safe to re-run on a schedule) | **✓** |
| GeoJSON valid | **✓** |

## Use cases
Emergency-management & public-safety situational awareness · newsroom / civic dashboards ·
911/EOC common operating picture · research — **without** paying for a hazard-data API or
sending anything to a vendor.

## Install
```bash
git clone https://github.com/cognis-digital/hazardwatch && cd hazardwatch
python -m pytest -q          # 14 tests
python -m hazardwatch demo
```

## Honest scope
Hazardwatch **aggregates and normalizes** authoritative feeds; it does not model or predict
hazards, and it inherits each provider's coverage, latency, and caveats. It is a defensive,
public-service situational-awareness tool. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

---
<p align="center">© 2026 Cognis Digital LLC · data © USGS / NASA / NOAA (public domain) · COCL-1.0</p>
