"""Normalized hazard event + ISO-time helper (pure stdlib).

Every source (USGS quakes, NASA EONET, NWS alerts, …) is normalized to one
`HazardEvent` so the dataset, map, and queries are source-agnostic. Severity is a
common 0–10 scale (earthquake magnitude for quakes; a mapped level for alerts).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import asdict, dataclass


@dataclass
class HazardEvent:
    id: str            # globally unique, "{source}:{source_id}"
    source: str        # usgs | eonet | nws | ...
    kind: str          # earthquake | wildfire | storm | volcano | flood | heat | tornado | other
    title: str
    ts: float          # epoch seconds (UTC)
    lat: float
    lon: float
    severity: float    # normalized 0..10
    url: str = ""
    raw_severity: str = ""

    def as_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return HazardEvent(**{k: d[k] for k in HazardEvent.__annotations__ if k in d})


def parse_iso(s: str) -> float:
    """Parse an ISO-8601 timestamp to epoch seconds. Works on Python 3.9+
    (normalizes trailing 'Z' which older fromisoformat rejects)."""
    if not s:
        return 0.0
    s = s.strip().replace("Z", "+00:00")
    try:
        dt = _dt.datetime.fromisoformat(s)
    except ValueError:
        # last resort: date only
        dt = _dt.datetime.fromisoformat(s[:10])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.timestamp()


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)
