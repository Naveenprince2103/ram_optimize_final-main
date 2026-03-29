"""
Flask Dashboard Server for RAM Sentinel
Provides REST API and web interface for monitoring.
"""
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import threading
import time
import shutil
import os
from pathlib import Path

# Import RAM Sentinel modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ram_sentinel.core.process_monitor import ProcessMonitor
from ram_sentinel.core.config import settings
from ram_sentinel.optimizer.tab_purger import TabPurger
from ram_sentinel.vault.manager import get_vault

app = Flask(__name__)
CORS(app)

# Global state
process_monitor = ProcessMonitor()
tab_purger = None
purger_running = False
vault = get_vault()
vault_mounted = False
connection_mode = 'offline'  # 'offline' or 'online'

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
    
    # Tab stats (if purger is running)
    if tab_purger and tab_purger.context:
        try:
            tabs = []
            for page in tab_purger.context.pages:
                try:
                    title = page.title if isinstance(page.title, str) else page.title()
                    url = page.url if isinstance(page.url, str) else page.url()
                    tabs.append({'title': title, 'url': url})
                except:
                    pass
            stats_cache['tabs'] = tabs
        except:
            stats_cache['tabs'] = []
    else:
        stats_cache['tabs'] = []
    
    stats_cache['last_update'] = time.time()

# API Endpoints
@app.route('/api/stats')
def get_stats():
    """Get all statistics."""
    update_stats()
    return jsonify({
        'system': stats_cache['system'],
        'processes': stats_cache['processes'],
        'tabs': stats_cache['tabs'],
        'purger_running': purger_running,
        'vault_mounted': vault_mounted,
        'connection_mode': connection_mode,
        'tab_count': len(stats_cache['tabs'])
    })

@app.route('/api/control/connection/<mode>', methods=['POST'])
def control_connection(mode):
    """Control the connection mode."""
    global connection_mode
    if mode in ['online', 'offline']:
        connection_mode = mode
        return jsonify({'status': 'success', 'mode': connection_mode})
    return jsonify({'error': 'invalid_mode'}), 400

@app.route('/api/system')
def get_system():
    """Get system RAM stats."""
    return jsonify(process_monitor.get_system_stats())

@app.route('/api/processes')
def get_processes():
    """Get top processes."""
    count = request.args.get('count', 15, type=int)
    return jsonify(process_monitor.get_top_processes(count))

@app.route('/api/tabs')
def get_tabs():
    """Get monitored tabs."""
    update_stats()
    return jsonify(stats_cache['tabs'])

@app.route('/api/control/optimizer/<action>', methods=['POST'])
def control_optimizer(action):
    """Control the tab optimizer."""
    global tab_purger, purger_running
    
    if action == 'start':
        if not purger_running:
            def run_purger():
                global tab_purger, purger_running
                try:
                    from playwright.sync_api import sync_playwright
                    tab_purger = TabPurger()
                    tab_purger.start_session(headless=True)
                    purger_running = True
                    
                    while purger_running:
                        try:
                            tab_purger.scan_and_purge(dry_run=False)
                            time.sleep(60)
                        except Exception as e:
                            print(f"Scan error: {e}")
                            if not purger_running:
                                break
                except Exception as e:
                    print(f"Purger error: {e}")
                    purger_running = False
            
            thread = threading.Thread(target=run_purger, daemon=True)
            thread.start()
            time.sleep(1)  # Give it a moment to start
            return jsonify({'status': 'started', 'message': 'Optimizer starting in background'})
        return jsonify({'status': 'already_running'})
    
    elif action == 'stop':
        if purger_running:
            purger_running = False
            time.sleep(1)  # Give it time to stop
            if tab_purger:
                try:
                    tab_purger.stop_session()
                except:
                    pass
            return jsonify({'status': 'stopped'})
        return jsonify({'status': 'not_running'})
    
    return jsonify({'error': 'invalid_action'}), 400

@app.route('/api/control/vault/<action>', methods=['POST'])
def control_vault(action):
    """Control the vault."""
    global vault_mounted
    
    if action == 'mount':
        try:
            mount_point = settings.DEFAULT_MOUNT_POINT_WIN
            size = settings.DEFAULT_VAULT_SIZE
            success = vault.mount(size, mount_point)
            if success:
                vault_mounted = True
                return jsonify({'status': 'mounted', 'mount_point': mount_point})
            return jsonify({'error': 'mount_failed'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif action == 'unmount':
        try:
            mount_point = settings.DEFAULT_MOUNT_POINT_WIN
            success = vault.unmount(mount_point)
            if success:
                vault_mounted = False
                return jsonify({'status': 'unmounted'})
            return jsonify({'error': 'unmount_failed'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'invalid_action'}), 400

@app.route('/api/control/process/kill/<int:pid>', methods=['POST'])
def kill_process(pid):
    """Kill a process."""
    if process_monitor.kill_process(pid):
        return jsonify({'status': 'killed', 'pid': pid})
    return jsonify({'error': 'kill_failed'}), 500

@app.route('/api/vault/stats')
def get_vault_stats():
    """Get detailed vault statistics."""
    mount_point = "R:\\" if os.name == 'nt' else "/mnt/ram_vault"
    
    if not os.path.exists(mount_point):
         return jsonify({"status": "unmounted"})
    
    try:
        total, used, free = shutil.disk_usage(mount_point)
        # Get count of files
        file_count = sum([len(files) for r, d, files in os.walk(mount_point)])
        
        return jsonify({
            "status": "mounted",
            "mount_point": mount_point,
            "total_size": total,
            "used_size": used,
            "free_size": free,
            "percent": (used/total) * 100,
            "file_count": file_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/')
def index():
    """Serve the dashboard."""
    return render_template('dashboard.html')

def run_server(host='127.0.0.1', port=5000):
    """Run the Flask server."""
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
