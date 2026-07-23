"""Minimal keyless HTTP JSON client (stdlib urllib). Only the `refresh` step
touches the network; everything else runs offline on the saved dataset."""

from __future__ import annotations

import json
import os
import urllib.request

UA = "hazardwatch/0.1 (+https://cognis.digital)"


class Client:
    def __init__(self, timeout: float = 30.0, offline: bool = False, cache_dir: str | None = None):
        self.timeout = timeout
        self.offline = offline
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def get_json(self, url: str):
        cache = os.path.join(self.cache_dir, _slug(url)) if self.cache_dir else None
        if self.offline:
            if cache and os.path.exists(cache):
                with open(cache, encoding="utf-8") as f:
                    return json.load(f)
            raise RuntimeError(f"offline and no cache for {url}")
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            raw = r.read().decode("utf-8", "replace")
        if cache:
            with open(cache, "w", encoding="utf-8") as f:
                f.write(raw)
        return json.loads(raw)


def _slug(url: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in url)[-120:] + ".json"
