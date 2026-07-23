"""Human-readable summary of the hazard dataset."""

from __future__ import annotations

from .store import stats


def summarize(events, top: int = 5) -> dict:
    s = stats(events)
    severe = sorted(events, key=lambda e: (e.severity, e.ts), reverse=True)[:top]
    s["most_severe"] = [{"kind": e.kind, "severity": e.severity, "title": e.title[:60],
                         "source": e.source} for e in severe]
    return s
