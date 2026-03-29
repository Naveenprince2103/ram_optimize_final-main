import psutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from .config import settings
from .logger import logger


DB_PATH = Path(settings.READ_LATER_DIR) / "memory_logs.db"


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                pid INTEGER,
                proc_name TEXT,
                proc_type TEXT,
                memory_mb REAL,
                cpu_percent REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_chrome_processes():
    """Return list of chrome-related processes with cmdline and memory info."""
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            name = (proc.info.get('name') or '').lower()
            if 'chrome' in name or 'msedge' in name or 'brave' in name:
                cmdline = ' '.join(proc.info.get('cmdline') or [])
                ptype = 'browser'
                if '--type=renderer' in cmdline:
                    ptype = 'renderer'

                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                cpu = proc.info.get('cpu_percent', 0.0)

                procs.append({
                    'pid': proc.info['pid'],
                    'name': proc.info.get('name'),
                    'cmdline': cmdline,
                    'type': ptype,
                    'memory_mb': mem_mb,
                    'cpu_percent': cpu
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x['memory_mb'], reverse=True)
    return procs


def get_chrome_memory_snapshot(log=False):
    """Get snapshot of chrome processes. Optionally log to sqlite."""
    snapshot = get_chrome_processes()
    if log:
        _ensure_db()
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            ts = datetime.utcnow().isoformat()
            for p in snapshot:
                cur.execute(
                    "INSERT INTO memory_logs (ts, pid, proc_name, proc_type, memory_mb, cpu_percent) VALUES (?,?,?,?,?,?)",
                    (ts, p['pid'], p['name'], p['type'], p['memory_mb'], p['cpu_percent'])
                )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to log memory snapshot: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    return snapshot


def get_recent_logs(limit=100):
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT ts, pid, proc_name, proc_type, memory_mb, cpu_percent FROM memory_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [
            {
                'ts': r[0], 'pid': r[1], 'name': r[2], 'type': r[3], 'memory_mb': r[4], 'cpu_percent': r[5]
            } for r in rows
        ]
    finally:
        conn.close()
