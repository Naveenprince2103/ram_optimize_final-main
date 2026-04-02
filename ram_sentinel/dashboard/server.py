"""
Flask Dashboard Server for RAM Sentinel
Provides REST API and web interface for monitoring.
"""
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import multiprocessing
import time
import shutil
import os
from pathlib import Path
import logging

# Import RAM Sentinel modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ram_sentinel.core.process_monitor import ProcessMonitor
from ram_sentinel.core.analyzer import get_chrome_memory_snapshot
from ram_sentinel.core.config import settings
from ram_sentinel.optimizer.tab_purger import TabPurger
from ram_sentinel.optimizer.tab_restoration import TabRestorationEngine
from ram_sentinel.vault.manager import get_vault
from ram_sentinel.core.memory_analyzer import MemoryAnalyzer
from ram_sentinel.core.leak_detector import leak_detector_service
from ram_sentinel.core.secure_sandbox import sandbox_service
from dashboard.utils import api_success, api_error, log_error
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state
process_monitor = ProcessMonitor()
tab_purger = None
purger_running = False
optimizer_process = None  # Multiprocessing.Process instead of threading
vault = get_vault()
vault_mounted = False
connection_mode = 'offline'  # 'offline' or 'online'

# Memory analyzer for Chrome summary
memory_analyzer = MemoryAnalyzer()

# Module 4 — Predictive Tab Restoration Engine
tab_restoration = TabRestorationEngine()

# Stats cache
stats_cache = {
    'system': {},
    'processes': [],
    'tabs': [],
    'last_update': 0
}

def update_stats():
    """Update statistics cache."""
    global stats_cache
    
    # System stats
    stats_cache['system'] = process_monitor.get_system_stats()
    
    # Top processes
    stats_cache['processes'] = process_monitor.get_top_processes(15)
    
    # Chrome/browser memory snapshot
    try:
        stats_cache['chrome_memory'] = get_chrome_memory_snapshot(log=False)
    except Exception:
        stats_cache['chrome_memory'] = []
    
    # Tab stats (if purger is running)
    if tab_purger and tab_purger.browser:
        try:
            tabs = []
            for context in tab_purger.browser.contexts:
                for page in context.pages:
                    try:
                        title = page.title if isinstance(page.title, str) else page.title()
                        url = page.url if isinstance(page.url, str) else page.url()
                        tabs.append({'title': title, 'url': url})
                    except:
                        pass
            stats_cache['tabs'] = tabs  # type: ignore
        except:
            stats_cache['tabs'] = []  # type: ignore
    else:
        stats_cache['tabs'] = []  # type: ignore
    
    stats_cache['last_update'] = time.time()  # type: ignore

# API Endpoints
@app.route('/api/stats')
def get_stats():
    """Get all statistics."""
    try:
        update_stats()
        return api_success(data={
            'system': stats_cache['system'],
            'processes': stats_cache['processes'],
            'tabs': stats_cache['tabs'],
            'purger_running': purger_running,
            'vault_mounted': vault_mounted,
            'connection_mode': connection_mode,
            'tab_count': len(stats_cache['tabs'])  # type: ignore
        })
    except PermissionError as e:
        log_error("Permission denied accessing system stats", e)
        return api_error(
            message="Permission denied accessing system information",
            error_code="PERMISSION_DENIED",
            status_code=403
        )
    except Exception as e:
        log_error("Failed to collect statistics", e)
        return api_error(
            message="Failed to collect statistics",
            error_code="STATS_COLLECTION_FAILED",
            status_code=500
        )

@app.route('/api/control/connection/<mode>', methods=['POST'])
def control_connection(mode):
    """Control the connection mode."""
    global connection_mode
    try:
        if mode not in ['online', 'offline']:
            return api_error(
                message=f"Invalid connection mode: {mode}",
                error_code="INVALID_MODE",
                status_code=400,
                details={'valid_modes': ['online', 'offline']}
            )
        
        connection_mode = mode
        logger.info(f"Connection mode changed to {mode}")
        
        return api_success(
            data={'mode': connection_mode},
            message=f'Connection mode set to {mode}'
        )
    except Exception as e:
        log_error(f"Connection control failed", e)
        return api_error(
            message="Failed to change connection mode",
            error_code="CONNECTION_CONTROL_FAILED",
            status_code=500
        )

@app.route('/api/system')
def get_system():
    """Get system RAM stats."""
    try:
        stats = process_monitor.get_system_stats()
        return api_success(data=stats)
    except PermissionError as e:
        log_error("Permission denied accessing system stats", e)
        return api_error(
            message="Permission denied accessing system information",
            error_code="PERMISSION_DENIED",
            status_code=403
        )
    except Exception as e:
        log_error("Failed to get system stats", e)
        return api_error(
            message="Failed to retrieve system statistics",
            error_code="SYSTEM_STATS_FAILED",
            status_code=500
        )


@app.route('/api/cpu')
def get_cpu():
    """Get CPU usage: per-core and total."""
    try:
        per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        total = psutil.cpu_percent(interval=None)
        return api_success(data={
            'per_core': per_core,
            'total': total,
            'timestamp': time.time()
        })
    except Exception as e:
        log_error("Failed to get CPU stats", e)
        return api_error(
            message="Failed to retrieve CPU statistics",
            error_code="CPU_STATS_FAILED",
            status_code=500
        )


@app.route('/api/memory_summary')
def memory_summary():
    """Get summarized Chrome memory usage for dashboard."""
    try:
        # Pass tab_purger if available so analyzer can optionally include
        # info about memory freed by purger (best-effort).
        summary = memory_analyzer.get_memory_summary(include_top=5, tab_purger_obj=tab_purger)
        return api_success(data=summary)
    except Exception as e:
        log_error("Failed to get memory summary", e)
        return api_error(
            message="Failed to retrieve memory summary",
            error_code="MEMORY_SUMMARY_FAILED",
            status_code=500
        )


@app.route('/api/system_summary')
def system_summary():
    """Module 3 – Memory Usage Analyzer: full structured summary.

    Returns system RAM, CPU and Chrome process data in one call.
    Front-end can use this as the primary memory-analyzer feed.
    """
    try:
        summary = memory_analyzer.get_memory_summary(include_top=5, tab_purger_obj=tab_purger)
        # Expose a flat 'system_memory' key as documented in the module spec
        summary['system_memory'] = summary.get('system', {})
        return api_success(data=summary)
    except Exception as e:
        log_error("Failed to get system summary", e)
        return api_error(
            message="Failed to retrieve system summary",
            error_code="SYSTEM_SUMMARY_FAILED",
            status_code=500
        )


@app.route('/api/top_processes')
def top_processes():
    """Return top N memory-consuming processes (default: 5)."""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        # Validate limit parameter
        if limit < 1 or limit > 50:
            return api_error(
                message="Limit must be between 1 and 50",
                error_code="INVALID_PARAMETER",
                status_code=400
            )
        
        procs = memory_analyzer.get_top_memory_processes(limit=limit)
        return api_success(data={'processes': procs, 'count': len(procs)})
    except ValueError as e:
        return api_error(
            message="Invalid limit parameter",
            error_code="INVALID_PARAMETER",
            status_code=400
        )
    except Exception as e:
        log_error("Failed to get top processes", e)
        return api_error(
            message="Failed to retrieve process list",
            error_code="TOP_PROCESSES_FAILED",
            status_code=500
        )


# ── Module 4: Predictive Tab Restoration ──────────────────────────────

@app.route('/api/restoration/predictions')
def restoration_predictions():
    """Return top predicted tabs the user is most likely to want restored."""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        if limit < 1 or limit > 20:
            return api_error(
                message="Limit must be between 1 and 20",
                error_code="INVALID_PARAMETER",
                status_code=400
            )
        
        predictions = tab_restoration.get_top_predictions(limit=limit)
        return api_success(data={
            'predictions': predictions,
            'count': len(predictions),
            'has_history': len(predictions) > 0
        })
    except ValueError as e:
        return api_error(
            message="Invalid limit parameter",
            error_code="INVALID_PARAMETER",
            status_code=400
        )
    except Exception as e:
        log_error("Failed to get restoration predictions", e)
        return api_error(
            message="Failed to retrieve restoration predictions",
            error_code="RESTORATION_PREDICTIONS_FAILED",
            status_code=500
        )


@app.route('/api/restoration/stats')
def restoration_stats():
    """Return restoration engine summary stats for the dashboard."""
    try:
        stats = tab_restoration.get_restoration_stats()
        return api_success(data=stats)
    except Exception as e:
        log_error("Failed to get restoration stats", e)
        return api_error(
            message="Failed to retrieve restoration statistics",
            error_code="RESTORATION_STATS_FAILED",
            status_code=500
        )


@app.route('/api/restoration/restore', methods=['POST'])
def restoration_restore():
    """Record that a user manually restored a tab."""
    try:
        body = request.get_json(force=True, silent=True) or {}
        url = (body.get('url') or '').strip()
        title = (body.get('title') or '').strip()
        
        if not url:
            return api_error(
                message="URL is required",
                error_code="MISSING_URL",
                status_code=400,
                details={'required_fields': ['url']}
            )
        
        if len(url) > 2048:
            return api_error(
                message="URL too long (max 2048 characters)",
                error_code="URL_TOO_LONG",
                status_code=400
            )
        
        tab_restoration.record_restore(url=url, title=title)
        logger.info(f"Recorded restoration of tab: {url}")
        
        return api_success(
            data={'url': url, 'title': title},
            message='Tab restoration recorded'
        )
    except ValueError as e:
        return api_error(
            message="Invalid request data",
            error_code="INVALID_REQUEST",
            status_code=400
        )
    except Exception as e:
        log_error("Failed to record restoration", e)
        return api_error(
            message="Failed to record tab restoration",
            error_code="RESTORATION_RECORD_FAILED",
            status_code=500
        )

@app.route('/api/processes')
def get_processes():
    """Get top processes."""
    try:
        count = request.args.get('count', 15, type=int)
        
        # Validate count parameter
        if count < 1 or count > 100:
            return api_error(
                message="Count must be between 1 and 100",
                error_code="INVALID_PARAMETER",
                status_code=400
            )
        
        processes = process_monitor.get_top_processes(count)
        return api_success(data=processes)
    except ValueError as e:
        return api_error(
            message="Invalid count parameter",
            error_code="INVALID_PARAMETER",
            status_code=400
        )
    except Exception as e:
        log_error("Failed to get processes", e)
        return api_error(
            message="Failed to retrieve process list",
            error_code="PROCESS_LIST_FAILED",
            status_code=500
        )

@app.route('/api/tabs')
def get_tabs():
    """Get monitored tabs."""
    try:
        update_stats()
        return api_success(data=stats_cache['tabs'])
    except Exception as e:
        log_error("Failed to get tabs", e)
        return api_error(
            message="Failed to retrieve tab list",
            error_code="TABS_LIST_FAILED",
            status_code=500
        )

def _run_purger_daemon():
    """
    Run the tab purger in a separate process.
    This function runs in a completely isolated Python process,
    making it thread-safe for Playwright operations.
    """
    try:
        from ram_sentinel.optimizer.tab_purger import TabPurger
        
        purger = TabPurger()
        purger.start_session(headless=True)
        
        # Keep running until process is terminated
        while True:
            try:
                purger.scan_and_purge(dry_run=False)
                time.sleep(60)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Purger scan error: {e}")
                time.sleep(60)
    except Exception as e:
        logger.error(f"Purger startup error: {e}")
    finally:
        try:
            purger.stop_session()
        except:
            pass

@app.route('/api/control/optimizer/<action>', methods=['POST'])
def control_optimizer(action):
    """
    Control the tab optimizer process.
    
    Uses multiprocessing.Process instead of threading for
    thread-safe Playwright browser automation.
    """
    global optimizer_process
    
    try:
        # Validate action parameter
        if action not in ['start', 'stop']:
            return api_error(
                message=f"Invalid optimizer action: {action}",
                error_code="INVALID_ACTION",
                status_code=400,
                details={'valid_actions': ['start', 'stop']}
            )
        
        if action == 'start':
            # Check if already running
            if optimizer_process and optimizer_process.is_alive():
                return api_success(
                    data={
                        'status': 'already_running',
                        'pid': optimizer_process.pid
                    },
                    message='Optimizer process already running'
                )
            
            # Start new process
            optimizer_process = multiprocessing.Process(
                target=_run_purger_daemon,
                name='TabPurgerOptimizer',
                daemon=False
            )
            optimizer_process.start()
            logger.info(f"Optimizer started with PID {optimizer_process.pid}")
            
            return api_success(
                data={
                    'status': 'started',
                    'pid': optimizer_process.pid,
                    'message': 'Optimizer starting in background'
                }
            )
        
        elif action == 'stop':
            if optimizer_process and optimizer_process.is_alive():
                # Gracefully terminate
                optimizer_process.terminate()
                optimizer_process.join(timeout=5)
                
                # Force kill if necessary
                if optimizer_process.is_alive():
                    optimizer_process.kill()
                    optimizer_process.join()
                
                logger.info("Optimizer process stopped")
                optimizer_process = None
                
                return api_success(
                    data={'status': 'stopped'},
                    message='Optimizer stopped'
                )
            
            return api_success(
                data={'status': 'not_running'},
                message='Optimizer is not running'
            )
    
    except Exception as e:
        log_error(f"Optimizer control failed for action '{action}'", e)
        return api_error(
            message="Failed to control optimizer",
            error_code="OPTIMIZER_CONTROL_FAILED",
            status_code=500
        )

@app.route('/api/control/vault/<action>', methods=['POST'])
def control_vault(action):
    """Control the vault (mount/unmount)."""
    global vault_mounted
    
    try:
        # Validate action
        if action not in ['mount', 'unmount']:
            return api_error(
                message=f"Invalid vault action: {action}",
                error_code="INVALID_ACTION",
                status_code=400,
                details={'valid_actions': ['mount', 'unmount']}
            )
        
        mount_point = settings.DEFAULT_MOUNT_POINT_WIN
        
        if action == 'mount':
            try:
                size = settings.DEFAULT_VAULT_SIZE
                success = vault.mount(size, mount_point)
                
                if success:
                    vault_mounted = True
                    logger.info(f"Vault mounted at {mount_point}")
                    return api_success(
                        data={
                            'status': 'mounted',
                            'mount_point': mount_point,
                            'size': size
                        },
                        message=f'Vault mounted at {mount_point}'
                    )
                
                return api_error(
                    message="Failed to mount vault",
                    error_code="MOUNT_FAILED",
                    status_code=500
                )
            except Exception as e:
                log_error("Vault mount failed", e)
                return api_error(
                    message=f"Vault mount failed: {str(e)}",
                    error_code="MOUNT_ERROR",
                    status_code=500
                )
        
        elif action == 'unmount':
            try:
                success = vault.unmount(mount_point)
                
                if success:
                    vault_mounted = False
                    logger.info(f"Vault unmounted from {mount_point}")
                    return api_success(
                        data={'status': 'unmounted'},
                        message=f'Vault unmounted from {mount_point}'
                    )
                
                return api_error(
                    message="Failed to unmount vault",
                    error_code="UNMOUNT_FAILED",
                    status_code=500
                )
            except Exception as e:
                log_error("Vault unmount failed", e)
                return api_error(
                    message=f"Vault unmount failed: {str(e)}",
                    error_code="UNMOUNT_ERROR",
                    status_code=500
                )
    
    except Exception as e:
        log_error(f"Vault control failed for action '{action}'", e)
        return api_error(
            message="Failed to control vault",
            error_code="VAULT_CONTROL_FAILED",
            status_code=500
        )

@app.route('/api/control/process/kill/<int:pid>', methods=['POST'])
def kill_process(pid):
    """Kill a process by PID."""
    try:
        if pid <= 0:
            return api_error(
                message="Invalid process ID",
                error_code="INVALID_PID",
                status_code=400
            )
        
        success = process_monitor.kill_process(pid)
        
        if success:
            logger.info(f"Process {pid} killed successfully")
            return api_success(
                data={'status': 'killed', 'pid': pid},
                message=f'Process {pid} terminated'
            )
        
        return api_error(
            message=f"Failed to kill process {pid}",
            error_code="KILL_FAILED",
            status_code=500
        )
    except PermissionError as e:
        log_error(f"Permission denied killing process {pid}", e)
        return api_error(
            message="Permission denied to kill process",
            error_code="PERMISSION_DENIED",
            status_code=403
        )
    except Exception as e:
        log_error(f"Failed to kill process {pid}", e)
        return api_error(
            message="Failed to kill process",
            error_code="KILL_FAILED",
            status_code=500
        )

@app.route('/api/vault/stats')
def get_vault_stats():
    """Get detailed vault statistics."""
    try:
        mount_point = "R:\\" if os.name == 'nt' else "/mnt/ram_vault"
        
        if not os.path.exists(mount_point):
            return api_success(data={"status": "unmounted"})
        
        try:
            total, used, free = shutil.disk_usage(mount_point)
            # Get count of files
            file_count = sum([len(files) for r, d, files in os.walk(mount_point)])
            
            return api_success(data={
                "status": "mounted",
                "mount_point": mount_point,
                "total_size": total,
                "used_size": used,
                "free_size": free,
                "percent": (used/total) * 100 if total > 0 else 0,
                "file_count": file_count
            })
        except OSError as e:
            log_error(f"Failed to access vault stats at {mount_point}", e)
            return api_error(
                message=f"Cannot access vault at {mount_point}",
                error_code="VAULT_ACCESS_DENIED",
                status_code=500
            )
    except Exception as e:
        log_error("Failed to get vault statistics", e)
        return api_error(
            message="Failed to retrieve vault statistics",
            error_code="VAULT_STATS_FAILED",
            status_code=500
        )

# --- Sandbox APIs ---
@app.route('/api/sandbox/status')
def sandbox_status():
    return api_success(data=sandbox_service.get_status())

@app.route('/api/sandbox/toggle', methods=['POST'])
def sandbox_toggle():
    new_state = sandbox_service.toggle()
    return api_success(data={'enabled': new_state})

@app.route('/api/sandbox/quarantine/<int:pid>', methods=['POST'])
def sandbox_quarantine(pid):
    success, msg = sandbox_service.quarantine_process(pid)
    if success:
        return api_success(data={'status': 'quarantined'}, message=msg)
    else:
        return api_error(message=msg, status_code=400)

@app.route('/api/sandbox/release/<int:pid>', methods=['POST'])
def sandbox_release(pid):
    success, msg = sandbox_service.release_process(pid)
    if success:
        return api_success(data={'status': 'released'}, message=msg)
    else:
        return api_error(message=msg, status_code=400)

# --- Leak Detector APIs ---
@app.route('/api/leak/scan', methods=['POST', 'GET'])
def leak_scan():
    try:
        report = leak_detector_service.scan_for_leaks()
        return api_success(data=report)
    except Exception as e:
        log_error("Leak scan failed", e)
        return api_error(message=str(e), status_code=500)

from ram_sentinel.core.system_optimizer import compact_memory, get_vram_info
from ram_sentinel.core.war_room import war_room

# --- System Optimizer APIs ---
@app.route('/api/optimizer/compact', methods=['POST'])
def run_compaction():
    try:
        report = compact_memory()
        msg = f"Compaction successful. Freed {report['freed_mb']} MB"
        return api_success(data=report, message=msg)
    except Exception as e:
        log_error("Compaction failed", e)
        return api_error(message=str(e), status_code=500)

@app.route('/api/optimizer/vram', methods=['GET'])
def run_vram_scan():
    try:
        report = get_vram_info()
        return api_success(data=report)
    except Exception as e:
        log_error("VRAM scan failed", e)
        return api_error(message=str(e), status_code=500)

# --- War Room APIs ---
@app.route('/api/control/war_room/toggle', methods=['POST'])
def toggle_war_room():
    try:
        body = request.get_json(force=True, silent=True) or {}
        target_game = body.get('target_game')
        
        is_active, logs = war_room.toggle_game_mode(target_game)
        
        return api_success(data={'active': is_active, 'logs': logs}, message="War Room mode toggled.")
    except Exception as e:
        log_error("War Room toggle failed", e)
        return api_error(message=str(e), status_code=500)

@app.route('/')
def index():

    """Serve the dashboard."""
    return render_template('dashboard.html')

def run_server(host='127.0.0.1', port=5000):
    """Run the Flask server."""
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
