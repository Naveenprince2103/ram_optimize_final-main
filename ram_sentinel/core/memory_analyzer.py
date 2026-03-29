"""Memory Usage Analyzer for RAM Sentinel.

This module provides a single, self-contained `MemoryAnalyzer` class used by
the dashboard. It avoids heavy blocking calls, handles process access
exceptions, and exposes a small set of methods consumed by the Flask server.
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from .logger import logger


class MemoryAnalyzer:
    def __init__(self, db_path: Optional[str] = None) -> None:
        base_dir = Path(__file__).parent
        self.db_path = str(db_path or (base_dir / "memory_logs.db"))
        # Prime cpu counters for better immediate readings
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        # Short-lived cache to reduce repeated psutil churn
        self._last_snapshot: List[Dict[str, Any]] = []
        self._last_snapshot_ts: float = 0.0

        self._ensure_db()

    def _ensure_db(self) -> None:
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_logs (
                    timestamp TEXT,
                    pid INTEGER,
                    type TEXT,
                    memory_mb REAL,
                    cpu_percent REAL
                )
                """
            )
            conn.commit()
        except Exception as e:
            logger.debug(f"_ensure_db error: {e}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def get_system_memory(self) -> Dict[str, float]:
        try:
            vm = psutil.virtual_memory()
            total_gb = vm.total / (1024 ** 3)
            used_gb = (vm.total - vm.available) / (1024 ** 3)
            return {"total_ram_gb": round(total_gb, 2), "used_ram_gb": round(used_gb, 2), "percent": round(vm.percent, 2)}
        except Exception:
            return {"total_ram_gb": 0.0, "used_ram_gb": 0.0, "percent": 0.0}

    def get_cpu_usage(self) -> Dict[str, float]:
        try:
            total = psutil.cpu_percent(interval=0.1)
            return {"total_percent": round(total, 2)}
        except Exception:
            return {"total_percent": 0.0}

    def get_chrome_processes(self) -> List[psutil.Process]:
        chrome_procs: List[psutil.Process] = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                info = proc.info
                name = (info.get("name") or "").lower()
                cmdline = info.get("cmdline") or []
                cmd = " ".join(cmdline) if isinstance(cmdline, (list, tuple)) else str(cmdline)
                if "chrome" in name or "chrome" in cmd.lower():
                    chrome_procs.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return chrome_procs

    def classify_process(self, proc: psutil.Process) -> str:
        try:
            cmdline = proc.cmdline() or []
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return "unknown"
        for arg in cmdline:
            if isinstance(arg, str) and "--type=renderer" in arg.lower():
                return "renderer"
            if isinstance(arg, str) and ("--type=gpu" in arg.lower() or "gpu-process" in arg.lower()):
                return "gpu"
        return "browser"

    def collect_memory_snapshot(self) -> List[Dict[str, Any]]:
        snapshot: List[Dict[str, Any]] = []
        procs = self.get_chrome_processes()
        for proc in procs:
            try:
                pid = proc.pid
                ptype = self.classify_process(proc)
                try:
                    mem_mb = proc.memory_info().rss / (1024 ** 2)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    mem_mb = 0.0
                try:
                    cpu = proc.cpu_percent(interval=0.0)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    cpu = 0.0
                snapshot.append({
                    "pid": int(pid),
                    "type": ptype,
                    "memory_mb": round(float(mem_mb), 2),
                    "cpu_percent": round(float(cpu), 2),
                    "name": proc.name() if hasattr(proc, "name") else "",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        # cache briefly
        try:
            self._last_snapshot = snapshot
            self._last_snapshot_ts = time.time()
        except Exception:
            pass

        return snapshot

    def log_to_database(self, snapshot: List[Dict[str, Any]]) -> None:
        if not snapshot:
            return
        ts = datetime.utcnow().isoformat()
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_logs (
                        timestamp TEXT,
                        pid INTEGER,
                        type TEXT,
                        memory_mb REAL,
                        cpu_percent REAL
                    )
                    """
                )
                rows = [(ts, int(s["pid"]), s.get("type", ""), float(s.get("memory_mb", 0.0)), float(s.get("cpu_percent", 0.0))) for s in snapshot]
                conn.executemany("INSERT INTO memory_logs (timestamp, pid, type, memory_mb, cpu_percent) VALUES (?, ?, ?, ?, ?)", rows)
        except Exception as e:
            logger.error(f"Failed to write memory logs to DB: {e}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def get_top_memory_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        procs: List[Dict[str, Any]] = []
        try:
            for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    mem = proc.info.get("memory_info")
                    rss = getattr(mem, "rss", 0) if mem else 0
                    procs.append({"name": proc.info.get("name") or "", "pid": int(proc.info.get("pid") or 0), "memory_mb": round(rss / (1024 ** 2), 2)})
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            procs.sort(key=lambda x: x["memory_mb"], reverse=True)
            return procs[:limit]
        except Exception:
            return []

    def get_memory_summary(self, include_top: int = 5, tab_purger_obj: Optional[object] = None) -> Dict[str, Any]:
        system = self.get_system_memory()
        cpu = self.get_cpu_usage()
        # Use cached snapshot if fresh (<1s)
        if self._last_snapshot and (time.time() - self._last_snapshot_ts) < 1.0:
            snapshot = self._last_snapshot
        else:
            snapshot = self.collect_memory_snapshot()

        total_chrome_mem = round(sum(item.get("memory_mb", 0.0) for item in snapshot), 2)
        renderer_count = sum(1 for item in snapshot if item.get("type") == "renderer")
        chrome_cpu = round(sum(item.get("cpu_percent", 0.0) for item in snapshot), 2)

        top_procs = self.get_top_memory_processes(limit=include_top)

        purger_freed_mb = None
        try:
            if tab_purger_obj is not None and hasattr(tab_purger_obj, "last_freed_memory_mb"):
                purger_freed_mb = float(getattr(tab_purger_obj, "last_freed_memory_mb"))
        except Exception:
            purger_freed_mb = None

        return {
            "system": system,
            "cpu": cpu,
            "chrome": {"total_memory_mb": total_chrome_mem, "renderer_count": int(renderer_count), "chrome_cpu_percent": chrome_cpu},
            "top_processes": top_procs,
            "purger_freed_mb": purger_freed_mb,
            "timestamp": time.time(),
        }

    def get_latest_memory_summary(self) -> Dict[str, Any]:
        s = self.get_memory_summary()
        return {"total_memory_mb": s["chrome"]["total_memory_mb"], "renderer_count": s["chrome"]["renderer_count"], "chrome_process_count": len(self._last_snapshot or []), "timestamp": s.get("timestamp")}


__all__ = ["MemoryAnalyzer"]
