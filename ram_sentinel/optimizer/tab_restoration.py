"""
Module 4 — Predictive Tab Restoration Engine
=============================================
Reads the Neural Tab Purger's saved history (index.json) and uses a
frequency × recency decay algorithm to predict which tabs the user is
most likely to want restored.

Algorithm:
    score = frequency × e^(−λ × days_since_last_purge)
    λ = 0.15  →  half-life ≈ 4.6 days, meaningful signal for ~2 weeks

No external dependencies beyond stdlib + the project's own config/logger.
"""

from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ..core.config import settings
from ..core.logger import logger


# Decay constant — tune to change how fast old tabs lose relevance
_LAMBDA = 0.15
_RESTORE_LOG_FILENAME = "restoration_log.json"


class TabRestorationEngine:
    """Predicts which purged tabs the user is most likely to want back."""

    def __init__(self, history_dir: Optional[str] = None) -> None:
        base = Path(history_dir or settings.READ_LATER_DIR)
        self.index_path: Path = base / "index.json"
        self.restore_log_path: Path = base / _RESTORE_LOG_FILENAME
        # Ensure directory exists
        base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_purged_history(self) -> List[Dict[str, Any]]:
        """Return every individual tab entry from the purge index."""
        if not self.index_path.exists():
            return []
        try:
            with open(self.index_path, "r", encoding="utf-8") as fh:
                batches = json.load(fh)
            tabs: List[Dict[str, Any]] = []
            for batch in batches:
                for tab in batch.get("tabs", []):
                    tabs.append(tab)
            return tabs
        except Exception as exc:
            logger.error(f"TabRestorationEngine: failed to load history: {exc}")
            return []

    def score_tabs(self, tabs: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Score each unique URL by: frequency × e^(−λ × days_old)
        Returns a list of dicts sorted by score descending.
        """
        if tabs is None:
            tabs = self.load_purged_history()

        if not tabs:
            return []

        restored_urls = self._load_restore_log()
        now_ts = time.time()

        # Aggregate per URL
        url_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"frequency": 0, "last_purge_ts": 0.0, "title": "", "url": ""}
        )

        for tab in tabs:
            url = (tab.get("url") or "").strip()
            if not url or url == "about:blank":
                continue
            ts = self._parse_timestamp(tab.get("timestamp", ""))
            entry = url_data[url]
            entry["frequency"] += 1
            entry["url"] = url
            # Keep the most recent title
            entry["title"] = tab.get("title") or entry["title"] or url
            if ts > entry["last_purge_ts"]:
                entry["last_purge_ts"] = ts

        scored: List[Dict[str, Any]] = []
        for url, data in url_data.items():
            days_old = max(0.0, (now_ts - data["last_purge_ts"]) / 86400.0)
            recency_factor = math.exp(-_LAMBDA * days_old)
            raw_score = data["frequency"] * recency_factor
            already_restored = url in restored_urls

            scored.append(
                {
                    "url": url,
                    "title": data["title"],
                    "domain": self._extract_domain(url),
                    "frequency": data["frequency"],
                    "days_since_purge": round(days_old, 1),
                    "score": round(raw_score, 4),
                    "score_pct": 0.0,  # normalised below
                    "already_restored": already_restored,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Normalise scores to 0-100 %
        max_score = scored[0]["score"] if scored else 1.0
        for item in scored:
            item["score_pct"] = round((item["score"] / max_score) * 100, 1)

        return scored

    def get_top_predictions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return the top `limit` restoration candidates."""
        return self.score_tabs()[:limit]

    def record_restore(self, url: str, title: str = "") -> None:
        """Persist a restoration event so the engine can learn over time."""
        log = self._load_restore_log_raw()
        log.append(
            {
                "url": url,
                "title": title,
                "restored_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        try:
            with open(self.restore_log_path, "w", encoding="utf-8") as fh:
                json.dump(log, fh, indent=2)
            logger.info(f"TabRestorationEngine: recorded restore for {url[:60]}")
        except Exception as exc:
            logger.error(f"TabRestorationEngine: failed to write restore log: {exc}")

    def get_restoration_stats(self) -> Dict[str, Any]:
        """High-level summary consumed by the dashboard stats row."""
        tabs = self.load_purged_history()
        scored = self.score_tabs(tabs)
        restore_log = self._load_restore_log_raw()

        unique_urls = len(scored)
        total_purges = len(tabs)
        restore_count = len(restore_log)

        top = scored[:3]

        return {
            "total_purged": total_purges,
            "unique_urls": unique_urls,
            "restore_sessions": restore_count,
            "top_predictions": top,
            "has_history": total_purges > 0,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_timestamp(self, ts_str: str) -> float:
        """Parse ISO timestamp string → Unix float. Returns 0 on failure."""
        if not ts_str:
            return 0.0
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return datetime.strptime(ts_str[:26], fmt).replace(
                    tzinfo=timezone.utc
                ).timestamp()
            except ValueError:
                continue
        return 0.0

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc or url[:30]
        except Exception:
            return url[:30]

    def _load_restore_log_raw(self) -> List[Dict[str, Any]]:
        if not self.restore_log_path.exists():
            return []
        try:
            with open(self.restore_log_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return []

    def _load_restore_log(self) -> set:
        """Return a set of URLs that have already been restored."""
        return {entry.get("url", "") for entry in self._load_restore_log_raw()}


__all__ = ["TabRestorationEngine"]
