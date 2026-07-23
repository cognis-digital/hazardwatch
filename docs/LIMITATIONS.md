# Limitations & honest scope

Hazardwatch **aggregates and normalizes** authoritative public feeds — it does not model,
rank, or predict hazards. Stated plainly:

- **Inherits provider coverage/latency/caveats.** USGS/NASA/NOAA define what exists, how
  fast, and how accurate; Hazardwatch only reflects it. Outages or schema changes upstream
  propagate here.
- **Severity is normalized, not authoritative.** Earthquake magnitude maps cleanly to 0–10;
  EONET events lack a magnitude (assigned a per-kind default); NWS severity is a 4-level
  mapping. Treat severity as a coarse triage aid, not a validated index.
- **`refresh` needs the network.** The core (query/map/report on the saved dataset) is
  offline; fetching new events is not. NWS requires a descriptive User-Agent (set).
- **Rolling window.** Default prune keeps 30 days; long-term history needs a larger window
  or an archive step.
- **Geometry simplification.** Polygon events are reduced to a centroid point for the map.
- **US-centric alerts.** NWS covers the US; global alerting would need additional feeds
  (GDACS, Copernicus EMS, etc.).

## Sensible extensions (kept out to stay zero-dependency)
- More feeds: NASA FIRMS active-fire, GDACS, USGS volcano/water, Copernicus.
- Alert-area polygons (not just centroids) and severity from CAP fields.
- De-duplication across sources (same event seen by USGS + EONET).
- A static HTML map viewer bundled with the GeoJSON.
