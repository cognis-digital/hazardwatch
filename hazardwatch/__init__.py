"""Hazardwatch — a self-updating public-safety hazard monitor from authoritative,
keyless open data (USGS earthquakes, NASA EONET wildfires/storms/volcanoes, NWS/NOAA
alerts).

`refresh` pulls the latest events from each feed and merges them (deduped) into a
maintained dataset; everything else — query, filter, map to GeoJSON, summarize —
runs offline on that dataset. Ships a GitHub Action so the dataset keeps itself
current with no server. Pure stdlib. By Cognis Digital.
"""

from __future__ import annotations

import os

__version__ = "0.1.0"
__all__ = ["event", "sources", "client", "store", "geo", "report", "cli"]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_DIR = os.path.join(_ROOT, "data", "samples")
DEFAULT_DATASET = os.path.join(_ROOT, "data", "hazards.json")
