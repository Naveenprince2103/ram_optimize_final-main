import psutil
import threading

class SecureSandbox:
    def __init__(self):
        self.enabled = False
        self.quarantined = {} # pid -> suspended Process
        self.lock = threading.Lock()
        
    def toggle(self, state=None):
        if state is None:
            self.enabled = not self.enabled
        else:
            self.enabled = state
            
        # If disabled, maybe release all quarantined? Keep simple for now.
        return self.enabled
        
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
                    'status': 'ISOLATED'
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
            'quarantined_count': len(self.quarantined),
            'active_containers': 1 if self.enabled else 0, # simulated global container count
            'processes': list(self.quarantined.values())
        }

sandbox_service = SecureSandbox()
