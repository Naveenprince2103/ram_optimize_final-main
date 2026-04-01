# UI Infrastructure - Detailed Technical Specification

## 📐 Current System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           dashboard.html (5000+ lines)              │   │
│  │  • HTML structure (inline in single file)           │   │
│  │  • CSS styling (5000+ lines inline)                 │   │
│  │  • JavaScript logic (polling every 3 seconds)       │   │
│  │  • HTML+CSS: Cyberpunk theme (#00f2ff primary)      │   │
│  │  • JS: Fetch /api/stats → Update DOM                │   │
│  └─────────────────────────────────────────────────────┘   │
│           ↓ HTTP Polling (every 3s)                         │
│           ↓ /api/stats, /api/processes, /api/tabs           │
│           ↓ JSON responses                                   │
└─────────────────────────────────────────────────────────────┘
          ↓↑                      ↓↑
┌─────────────────────────────────────────────────────────────┐
│                    Flask Server (port 5000)                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Routes in server.py (1400+ lines)                     │ │
│  │ ├─ /api/stats              → ProcessMonitor           │ │
│  │ ├─ /api/processes          → ProcessMonitor           │ │
│  │ ├─ /api/tabs               → TabPurger               │ │
│  │ ├─ /api/control/optimizer  → Threading (❌ ISSUE!)   │ │
│  │ ├─ /api/control/vault      → VaultManager            │ │
│  │ └─ /api/restoration/...    → TabRestorationEngine    │ │
│  └───────────────────────────────────────────────────────┘ │
│           ↓                                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ RAM Sentinel Core Modules                             │ │
│  │ ├─ ProcessMonitor (get_system_stats)                 │ │
│  │ ├─ MemoryAnalyzer (Chrome memory breakdown)          │ │
│  │ ├─ TabPurger (Browser automation - Playwright)       │ │
│  │ │   └─→ Launched in Flask thread (❌ UNSAFE!)        │ │
│  │ ├─ TabRestorationEngine (prediction model)           │ │
│  │ └─ VaultManager (encrypted storage)                  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
          ↓ System calls
┌─────────────────────────────────────────────────────────────┐
│                   Windows OS / psutil                       │
│ - RAM usage, CPU, processes                                 │
│ - Chrome process info                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 THREADING ISSUE - Root Cause

```python
# CURRENT PROBLEMATIC CODE (server.py, line ~330)

@app.route('/api/control/optimizer/<action>', methods=['POST'])
def control_optimizer(action):
    global tab_purger, purger_running
    
    if action == 'start':
        if not purger_running:
            # ❌ PROBLEM: Creating new thread from Flask request handler
            thread = threading.Thread(target=_run_purger_daemon, daemon=True)
            thread.start()
            # ... Flask thread continues, but Playwright thread is now running
            #     Playwright accesses browser resources not thread-safe
            #     Result: Hangs, crashes, or both!
            return jsonify({'status': 'started'})

def _run_purger_daemon():
    global tab_purger, purger_running
    from playwright.sync_api import sync_playwright
    tab_purger = TabPurger()
    # ❌ Playwright is synchronous-only in nested threads
    # ❌ GIL (Global Interpreter Lock) contention
    # ❌ Flask might handle next request while browser is initializing
    tab_purger.start_session(headless=True)
    purger_running = True
    while purger_running:
        tab_purger.scan_and_purge(dry_run=False)
        time.sleep(60)
```

### **Why This Fails**
- Playwright's sync API expects single-threaded execution
- Flask might process another request while Playwright is initializing browser
- Browser resources (memory, handles) are not thread-safe
- GIL contention causes unpredictable behavior

### **Root Problem Flow**
```
1. User clicks "Start Optimizer" in dashboard
   ↓
2. Flask request handler: /api/control/optimizer/start
   ↓
3. Creates new Thread → Launches _run_purger_daemon()
   ↓
4. Playwright tries to spawn browser.exe process
   ↓
5. Meanwhile, Flask is already accepting next HTTP request
   ↓
6. Two threads competing for browser resources
   ↓
7. CRASH: "Cannot create process" or "Connection refused"
```

---

## ✅ SOLUTION 1: Use multiprocessing (Recommended)

```python
# FIXED CODE OPTION A: Use multiprocessing.Process

import multiprocessing
import signal
import os

optimizer_process = None

@app.route('/api/control/optimizer/<action>', methods=['POST'])
def control_optimizer(action):
    global optimizer_process
    
    if action == 'start':
        if optimizer_process is None or not optimizer_process.is_alive():
            # ✅ SAFE: Create separate process, not thread
            optimizer_process = multiprocessing.Process(
                target=_run_purger_daemon,
                name='TabPurgerProcess',
                daemon=False  # We manage lifecycle explicitly
            )
            optimizer_process.start()
            return api_response(
                data={'status': 'started', 'pid': optimizer_process.pid}
            )
        return api_response(data={'status': 'already_running'})
    
    elif action == 'stop':
        if optimizer_process and optimizer_process.is_alive():
            # ✅ SAFE: Terminate process cleanly
            optimizer_process.terminate()
            optimizer_process.join(timeout=5)  # Wait max 5 seconds
            if optimizer_process.is_alive():
                optimizer_process.kill()  # Force kill if needed
            optimizer_process = None
            return api_response(data={'status': 'stopped'})
        return api_response(data={'status': 'not_running'})
    
    return api_response(
        error='invalid_action',
        status=400
    )

def _run_purger_daemon():
    """Runs in separate process - safe from Flask thread interference."""
    try:
        from ram_sentinel.optimizer.tab_purger import TabPurger
        
        tab_purger = TabPurger()
        tab_purger.start_session(headless=True)
        
        # Keep running until process is terminated
        while True:
            tab_purger.scan_and_purge(dry_run=False)
            time.sleep(60)
    except Exception as e:
        print(f"Purger daemon error: {e}")
    finally:
        try:
            tab_purger.stop_session()
        except:
            pass
```

**Advantages**:
- ✅ Completely isolated from Flask
- ✅ Playwright works reliably
- ✅ Simple, minimal changes
- ✅ No extra dependencies

**Disadvantages**:
- ⚠️ Cannot access browser state from Flask directly
- ⚠️ Need IPC (inter-process communication) for status

---

## ✅ SOLUTION 2: Use Celery (For Large Scale)

```python
# FIXED CODE OPTION B: Use Celery for task queue

from celery import Celery
import os

# Initialize Celery
celery_app = Celery(__name__)
celery_app.conf.broker_url = 'redis://localhost:6379'
celery_app.conf.result_backend = 'redis://localhost:6379'

@celery_app.task(name='run_optimizer')
def run_optimizer_task():
    """Runs optimizer in Celery worker process."""
    from ram_sentinel.optimizer.tab_purger import TabPurger
    
    try:
        tab_purger = TabPurger()
        tab_purger.start_session(headless=True)
        
        while True:  # Until task is revoked
            tab_purger.scan_and_purge(dry_run=False)
            time.sleep(60)
    except Exception as e:
        print(f"Optimizer task error: {e}")
    finally:
        try:
            tab_purger.stop_session()
        except:
            pass

@app.route('/api/control/optimizer/<action>', methods=['POST'])
def control_optimizer(action):
    if action == 'start':
        # Check if task already running
        active_tasks = celery_app.control.inspect().active()
        if any(active_tasks.values()):
            return api_response(data={'status': 'already_running'})
        
        # Start new task
        task = run_optimizer_task.delay()
        return api_response(data={
            'status': 'started',
            'task_id': task.id
        })
    
    elif action == 'stop':
        # Revoke all running tasks
        celery_app.control.revoke(force_terminate=True, terminate=True)
        return api_response(data={'status': 'stopped'})
    
    return api_response(error='invalid_action', status=400)
```

**Advantages**:
- ✅ Scales to many tasks
- ✅ Persistent task queue
- ✅ Built-in retry logic
- ✅ Monitoring capabilities

**Disadvantages**:
- ❌ Requires Redis server
- ❌ More complex setup
- ❌ Overkill for single process

---

## 🔧 CHANGE #2: API Response Standardization

### **Current Inconsistent Responses**
```javascript
// All these different formats exist now (❌ Bad)

// Optimizer start
HTTP 200
{
  "status": "started",
  "message": "Optimizer starting in background"
}

// Vault mount
HTTP 200
{
  "status": "mounted",
  "mount_point": "V:"
}

// Error
HTTP 400
{
  "error": "invalid_mode"
}

// Tab restoration
HTTP 200
{
  "status": "recorded",
  "url": "https://example.com"
}
```

### **Required Standardized Response**
```javascript
// ALL endpoints return this format (✅ Good)

SUCCESS (HTTP 200):
{
  "success": true,
  "data": {
    "status": "started",
    "message": "Optimizer starting in background",
    "timestamp": "2024-01-15T10:30:45Z"
  },
  "error": null,
  "error_code": null
}

ERROR (HTTP 400):
{
  "success": false,
  "data": null,
  "error": "Invalid mode parameter",
  "error_code": "INVALID_MODE",
  "details": {
    "field": "mode",
    "expected": ["online", "offline"],
    "received": "purple"
  }
}

NOT FOUND (HTTP 404):
{
  "success": false,
  "data": null,
  "error": "Resource not found",
  "error_code": "NOT_FOUND"
}

SERVER ERROR (HTTP 500):
{
  "success": false,
  "data": null,
  "error": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "trace_id": "ae3b5c2e-4f1a-4b9d-8c2a-1e5f3a7b9c1d"
}
```

### **Implementation**
```python
# Create helpers in utils/response.py

from flask import jsonify
from datetime import datetime
import uuid

def api_success(data=None, status_code=200):
    """Return standardized success response."""
    return jsonify({
        'success': True,
        'data': data,
        'error': None,
        'error_code': None,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), status_code

def api_error(message, error_code=None, status_code=400, details=None):
    """Return standardized error response."""
    return jsonify({
        'success': False,
        'data': None,
        'error': message,
        'error_code': error_code or 'UNKNOWN_ERROR',
        'details': details,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'trace_id': str(uuid.uuid4())
    }), status_code

# Usage in endpoints:
@app.route('/api/stats')
def get_stats():
    try:
        update_stats()
        return api_success(data={
            'system': stats_cache['system'],
            'processes': stats_cache['processes'],
            'tabs': stats_cache['tabs']
        })
    except PermissionError as e:
        return api_error(
            message="Permission denied accessing process information",
            error_code="PERMISSION_DENIED",
            status_code=403
        )
    except Exception as e:
        log.error(f"Stats collection failed: {e}", exc_info=True)
        return api_error(
            message="Failed to collect statistics",
            error_code="STATS_COLLECTION_FAILED",
            status_code=500
        )
```

---

## 🎨 CHANGE #3: CSS Refactoring

### **Current Structure (❌ Problematic)**
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 5000+ lines of CSS inline */
        :root { --bg-dark: #0b0c15; ... }
        body { ... } /* 10,000s of rules */
        .dashboard-grid { ... }
        /* Everything in one file */
    </style>
</head>
<body>
    <!-- 3000+ lines of HTML -->
    <script>
        /* 2000+ lines of JavaScript inline */
    </script>
</body>
</html>
```

**Problems**:
- ❌ Unmaintainable (80KB single file)
- ❌ CSS not cached (redownloaded each pageload)
- ❌ JavaScript not cached either
- ❌ Hard to change theme
- ❌ Styling conflicts likely

### **Required Structure (✅ Maintainable)**
```
dashboard/
├── templates/
│   ├── base.html (common structure)
│   ├── dashboard.html (main dashboard)
│   ├── settings.html (settings page)
│   └── analytics.html (analytics page)
├── static/
│   ├── css/
│   │   ├── main.css (load this one, imports others)
│   │   ├── design-system.css (colors, typography)
│   │   │   :root { --primary: #00f2ff; ... }
│   │   │   h1 { font-family: Orbitron; }
│   │   │
│   │   ├── layout.css (grid, spacing)
│   │   │   :root { --grid-cols: 12; --gap: 20px; }
│   │   │   .dashboard-grid { ... }
│   │   │
│   │   ├── components.css (buttons, cards, tables)
│   │   │   .btn { ... }
│   │   │   .card { ... }
│   │   │   .table { ... }
│   │   │
│   │   ├── animations.css (keyframes, transitions)
│   │   │   @keyframes fadeIn { ... }
│   │   │
│   │   └── responsive.css (media queries)
│   │       @media (max-width: 768px) { ... }
│   │
│   └── js/
│       ├── app.js (main app controller)
│       │   - Bootstrap app
│       │   - Initialize event listeners
│       │
│       ├── api.js (API client)
│       │   - fetch() wrappers
│       │   - Error handling
│       │
│       ├── ui.js (DOM manipulation)
│       │   - Update stats display
│       │   - Toggle buttons
│       │   - Show notifications
│       │
│       ├── cache.js (client-side caching)
│       │   - LocalStorage
│       │   - Session data
│       │
│       └── utils.js (helpers)
│           - Formatting
│           - Validation
```

### **CSS Optimization**
```css
/* main.css */
@import url('design-system.css');
@import url('layout.css');
@import url('components.css');
@import url('animations.css');
@import url('responsive.css');
```

Then Gzip compresses to ~40KB (vs 80KB inline).

---

## 📊 CHANGE #4: Data Persistence (SQLite)

### **Database Schema**
```sql
-- System Statistics (hourly, 30-day retention)
CREATE TABLE system_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ram_total_mb INTEGER NOT NULL,
    ram_used_mb INTEGER NOT NULL,
    ram_percent REAL NOT NULL,
    cpu_percent REAL NOT NULL,
    disk_total_mb INTEGER NOT NULL,
    disk_used_mb INTEGER NOT NULL,
    disk_percent REAL NOT NULL
);
CREATE INDEX idx_timestamp ON system_stats(timestamp);

-- Process History (every 5 minutes)
CREATE TABLE process_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    memory_mb REAL NOT NULL,
    cpu_percent REAL NOT NULL
);
CREATE INDEX idx_process_timestamp ON process_history(process_name, timestamp);

-- Tab History (every 10 seconds when purger running)
CREATE TABLE tab_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    memory_mb REAL,
    was_purged BOOLEAN DEFAULT 0
);
CREATE INDEX idx_tab_timestamp ON tab_history(timestamp);

-- Restoration Events
CREATE TABLE restoration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    action TEXT NOT NULL, -- 'predict', 'restore', 'auto_restore'
    reason TEXT
);

-- Clean up old data
CREATE TRIGGER cleanup_old_stats
AFTER INSERT ON system_stats
BEGIN
  DELETE FROM system_stats 
  WHERE timestamp < datetime('now', '-30 days');
END;
```

### **API Endpoints for Analytics**
```python
@app.route('/api/analytics/system-trends')
def system_trends():
    """Get 24-hour system trend data."""
    hours = request.args.get('hours', 24, type=int)
    
    query = """
      SELECT timestamp, ram_percent, cpu_percent
      FROM system_stats
      WHERE timestamp > datetime('now', f'-{hours} hours')
      ORDER BY timestamp ASC
    """
    
    return api_success(data=execute_query(query))

@app.route('/api/analytics/top-processes')
def top_processes_history():
    """Get top memory-consuming processes over time."""
    days = request.args.get('days', 7, type=int)
    
    query = """
      SELECT process_name, AVG(memory_mb) as avg_memory,
             MAX(memory_mb) as peak_memory, COUNT(*) as samples
      FROM process_history
      WHERE timestamp > datetime('now', f'-{days} days')
      GROUP BY process_name
      ORDER BY peak_memory DESC
      LIMIT 10
    """
    
    return api_success(data=execute_query(query))

@app.route('/api/analytics/tab-stats')
def tab_statistics():
    """Get tab activity statistics."""
    days = request.args.get('days', 7, type=int)
    
    query = """
      SELECT COUNT(*) as total_tabs,
             SUM(CASE WHEN was_purged=1 THEN 1 ELSE 0 END) as purged,
             AVG(memory_mb) as avg_memory,
             MAX(memory_mb) as peak_memory
      FROM tab_history
      WHERE timestamp > datetime('now', f'-{days} days')
    """
    
    return api_success(data=execute_query(query))
```

---

## ⚡ CHANGE #5: WebSocket Implementation

### **Current (Polling Every 3 Seconds)**
```javascript
// Current - HTTP polling (inefficient)
setInterval(async () => {
    const res = await fetch('/api/stats');
    const data = await res.json();
    updateDashboard(data);
}, 3000);  // Every 3 seconds
```

**Problems**:
- Request every 3 seconds even if data unchanged
- 20 HTTP requests per minute
- 5-second delay possible (if request takes 2s)
- 80KB/hour data transfer

### **Required (WebSocket)**
```javascript
// Required - WebSocket (efficient)
const socket = io('http://localhost:5000', {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5
});

socket.on('connect', () => {
    console.log('Connected to dashboard server');
    showNotification('Connected', 'success');
});

socket.on('stats_update', (data) => {
    updateDashboard(data);
    console.log('Stats updated:', data.timestamp);
});

socket.on('error_alert', (message) => {
    showNotification(message, 'error');
});

socket.on('disconnect', () => {
    showNotification('Disconnected from server', 'warning');
});

// Send commands via WebSocket
function startOptimizer() {
    socket.emit('control_optimizer', {action: 'start'}, (response) => {
        if (response.success) {
            showNotification('Optimizer started', 'success');
        } else {
            showNotification('Failed: ' + response.error, 'error');
        }
    });
}
```

### **Backend Implementation**
```python
from flask import Flask
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

connected_clients = {}

@socketio.on('connect')
def handle_connect():
    """Client connected."""
    connected_clients[request.sid] = {
        'connected_at': datetime.now(),
        'stats_mode': 'basic'  # 'basic' or 'detailed'
    }
    emit('message', {'data': 'Connected to server'})
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected."""
    if request.sid in connected_clients:
        del connected_clients[request.sid]
    print(f"Client disconnected: {request.sid}")

@socketio.on('control_optimizer')
def control_optimizer_socket(data):
    """Handle optimizer control via WebSocket."""
    action = data.get('action')
    if action not in ['start', 'stop']:
        emit('error_alert', {'message': 'Invalid action'})
        return
    
    try:
        if action == 'start':
            # Start optimizer
            global optimizer_process
            optimizer_process = Process(target=_run_purger_daemon)
            optimizer_process.start()
            emit('response', {'success': True, 'data': 'Started'})
            broadcast_to_all('optimizer_state_change', {'running': True})
        else:
            # Stop optimizer
            optimizer_process.terminate()
            emit('response', {'success': True, 'data': 'Stopped'})
            broadcast_to_all('optimizer_state_change', {'running': False})
    except Exception as e:
        emit('response', {'success': False, 'error': str(e)})

# Emit stats to all connected clients every 1 second
@socketio.on_event()
def emit_stats_loop():
    """Background task to emit stats."""
    while True:
        try:
            update_stats()
            socketio.emit('stats_update', {
                'system': stats_cache['system'],
                'processes': stats_cache['processes'],
                'tabs': stats_cache['tabs'],
                'timestamp': datetime.now().isoformat()
            })
            time.sleep(1)
        except Exception as e:
            print(f"Stats emission failed: {e}")
            time.sleep(5)

def broadcast_to_all(event, data):
    """Emit event to all connected clients."""
    socketio.emit(event, data, broadcast=True)

if __name__ == '__main__':
    # Start background stats thread
    stats_thread = Thread(target=emit_stats_loop, daemon=True)
    stats_thread.start()
    
    socketio.run(app, host='127.0.0.1', port=5000)
```

---

## 📈 Performance Comparison

| Metric | HTTP Polling (Current) | WebSocket (Proposed) |
|--------|----------------------|----------------------|
| Requests/minute | 20 | 1 |
| Latency (avg) | 2-3s | 100-200ms |
| Latency (99th %ile) | 5-8s | 500ms |
| Data transfer/hour | 80KB | 10KB |
| CPU overhead | ~5% | ~1% |
| Memory overhead | 2MB | 1MB |
| Connection setup | 100ms | 50ms |
| Reconnect time | ~3s | <100ms |
| Real-time feel | Sluggish | Snappy |

---

## 📱 Mobile Responsiveness

### **Current Layout (30% responsive)**
```
Desktop (1920px): ✅ Perfect
  ┌─────────────────────────────────────┐
  │ [≡] SENTINEL  [📊] [⚙️]  [🔔]       │
  ├─────────────────────────────────────┤
  │ [Stats] [Stats] [Stats] [Stats]     │
  │ [          Main Chart        ] [Act]│
  │ [  Processes      ] [  Tabs  ]      │
  └─────────────────────────────────────┘

Mobile (375px): ❌ Broken
  ┌─────────────┐
  │ [≡] S [🔔]  │
  ├─────────────┤
  │ [Stats....] │  Stats extremely narrow
  │ [Stats....] │  Charts unreadable
  │ [Stats....] │  Buttons overlapping
  │ [Stats....] │  Horizontal scroll needed
  └─────────────┘
```

### **Required Mobile Layout**
```
Mobile (375px): ✅ Optimized
  ┌─────────────┐
  │ [≡] S [🔔]  │
  ├─────────────┤
  │ ┌─────────┐ │
  │ │ RAM:80% │ │  Full width cards
  │ └─────────┘ │  Single col layout
  │ ┌─────────┐ │
  │ │CPU: 45% │ │
  │ └─────────┘ │
  │ ┌─────────┐ │
  │ │ [Chart] │ │
  │ └─────────┘ │
  │ ┌─────────┐ │
  │ │Process..│ │
  │ │- Chrome │ │
  │ │- Edge   │ │
  │ └─────────┘ │
  └─────────────┘
```

---

## 🎓 Summary of Changes

| # | Change | Files | Effort | Impact |
|---|--------|-------|--------|--------|
| 1 | Fix threading (Process) | server.py | 2h | 🔴 CRITICAL |
| 2 | Response standardization | server.py, utils/ | 3h | 🔴 CRITICAL |
| 3 | Error handling | all routes | 4h | 🔴 CRITICAL |
| 4 | Loading indicators | dashboard.html, app.js | 2h | 🟡 HIGH |
| 5 | CSS refactoring | templates/, static/ | 4h | 🟡 HIGH |
| 6 | Database persistence | models/, new tables | 6h | 🟡 HIGH |
| 7 | WebSocket real-time | server.py, app.js | 5h | 🟡 HIGH |
| 8 | Mobile responsive | dashboard.html, responsive.css | 4h | 🟢 MEDIUM |
| 9 | Navigation routing | app.js, server.py | 3h | 🟢 MEDIUM |
| 10 | Accessibility | all HTML | 3h | 🟢 MEDIUM |

**Total**: ~36 hours for comprehensive modernization

---

**Version**: 3.0  
**Status**: Detailed technical specification  
**Ready for**: Development team implementation
