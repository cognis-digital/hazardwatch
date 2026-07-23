"""The maintained hazard dataset: load / merge (dedupe) / prune / save.

Merge is idempotent and additive — re-running `refresh` only adds genuinely new
events and refreshes existing ones by id, so a scheduled job keeps the dataset
current without duplicating. This is the reusable "static dataset → self-updating"
pattern for any Cognis data repo.
"""

from __future__ import annotations

import json
import os

from .event import HazardEvent

DAY = 86400.0


def load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("events", data) if isinstance(data, dict) else data
    return [HazardEvent.from_dict(d) for d in rows]


def save(path: str, events: list) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {"events": [e.as_dict() for e in sort_recent(events)],
               "count": len(events)}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def merge(existing: list, incoming: list) -> tuple:
    """Return (merged, n_added). Dedup by id; incoming refreshes existing."""
    by_id = {e.id: e for e in existing}
    added = 0
    for e in incoming:
        if e.id not in by_id:
            added += 1
        by_id[e.id] = e   # incoming is fresher — overwrite
    return sort_recent(by_id.values()), added


def prune(events, max_age_days: float, now_ts: float) -> list:
    """Drop events older than max_age_days (events with ts<=0 are kept)."""
    cutoff = now_ts - max_age_days * DAY
    return [e for e in events if e.ts <= 0 or e.ts >= cutoff]


def sort_recent(events) -> list:
    return sorted(events, key=lambda e: e.ts, reverse=True)


def stats(events) -> dict:
    from collections import Counter
    return {"total": len(events),
            "by_kind": dict(Counter(e.kind for e in events).most_common()),
            "by_source": dict(Counter(e.source for e in events).most_common())}
