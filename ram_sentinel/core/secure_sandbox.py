import psutil
import threading
import time

class SecureSandbox:
    def __init__(self):
        self.enabled = False
        self.auto_sandbox_enabled = False
        self.quarantined = {} # pid -> suspended Process
        self.lock = threading.Lock()
        self.whitelist = ['chrome.exe', 'brave.exe', 'firefox.exe', 'code.exe', 'explorer.exe', 'python.exe', 'node.exe', 'pycharm.exe', 'devenv.exe', 'msmpeng.exe']
        self.monitor_thread = None
        
    def toggle(self, state=None):
        if state is None:
            self.enabled = not self.enabled
        else:
            self.enabled = state
            
        if self.enabled:
            self.start_auto_monitor()
        else:
            self.stop_auto_monitor()
            
        return self.enabled
        
    def start_auto_monitor(self):
        self.auto_sandbox_enabled = True
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
    def stop_auto_monitor(self):
        self.auto_sandbox_enabled = False
        
    def _monitor_loop(self):
        history = {}
        while self.auto_sandbox_enabled:
            try:
                # Track memory changes to find massive sudden leaks in non-whitelisted apps
                for p in psutil.process_iter(['name', 'memory_info']):
                    try:
                        pid = p.pid
                        name = p.info['name'].lower() if p.info['name'] else "unknown"
                        mem_mb = p.info['memory_info'].rss / (1024 * 1024) if p.info['memory_info'] else 0
                        
                        if name in self.whitelist:
                            continue
                            
                        # If a non-whitelisted app suddenly jumps over 400MB, Auto-Quarantine!
                        if mem_mb > 400:
                            if pid not in history or mem_mb > history.get(pid, 0) + 150:
                                # Rapid unexpected growth detected!
                                with self.lock:
                                    if pid not in self.quarantined:
                                        # Use the class method to correctly suspend
                                        # Temporarily release lock to call quarantine_process
                                        pass
                                self.quarantine_process(pid)
                                        
                        history[pid] = mem_mb
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        if pid in history: del history[pid]
                        pass
                        
                # Purge history of dead processes to avoid unbounded memory growth
                active_pids = set(psutil.pids())
                history = {k: v for k, v in history.items() if k in active_pids}
                
                time.sleep(3) # Check stats every 3 seconds
            except Exception as e:
                time.sleep(5)
                
    def quarantine_process(self, pid):
        if not self.enabled:
            return False, "Sandbox is disabled."
            
        try:
            with self.lock:
                if pid in self.quarantined:
                    return False, "Process already quarantined."
                proc = psutil.Process(pid)
                proc.suspend()
                self.quarantined[pid] = {
                    'pid': pid,
                    'name': proc.name(),
                    'memory_mb': round(proc.memory_info().rss / (1024*1024), 2),
                    'status': 'ISOLATED (Auto)'
                }
            return True, f"Suspended and isolated PID {pid}."
        except psutil.NoSuchProcess:
            return False, f"Process {pid} no longer exists."
        except psutil.AccessDenied:
            return False, f"Access denied isolating PID {pid}."
        except Exception as e:
            return False, f"Error: {e}"

    def release_process(self, pid):
        try:
            with self.lock:
                if pid not in self.quarantined:
                    return False, "Not in quarantine."
                    
                proc = psutil.Process(pid)
                proc.resume()
                del self.quarantined[pid]
                
            return True, f"Released PID {pid} from sandbox."
        except psutil.NoSuchProcess:
            with self.lock:
                del self.quarantined[pid]
            return False, "Process died while in sandbox."
        except Exception as e:
            return False, f"Error releasing: {e}"

    def get_status(self):
        # cleanup dead processes
        with self.lock:
            dead_pids = []
            for pid in self.quarantined:
                if not psutil.pid_exists(pid):
                    dead_pids.append(pid)
            for pid in dead_pids:
                del self.quarantined[pid]
                
        return {
            'enabled': self.enabled,
            'auto_sandbox_active': self.auto_sandbox_enabled,
            'quarantined_count': len(self.quarantined),
            'active_containers': 1 if self.enabled else 0, # simulated global container count
            'processes': list(self.quarantined.values())
        }

sandbox_service = SecureSandbox()
