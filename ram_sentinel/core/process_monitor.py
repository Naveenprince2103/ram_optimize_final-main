"""
Process Monitor for RAM Sentinel
Monitors all system processes and identifies RAM hogs.
"""
import psutil
from datetime import datetime
from ..core.logger import logger

class ProcessMonitor:
    def __init__(self):
        self.threshold_mb = 500  # Alert if process uses > 500MB
        # Prime CPU counter
        try:
            psutil.cpu_percent(interval=None)
        except:
            pass
        
    def get_all_processes(self):
        """Get all running processes with RAM usage."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                mem_mb = info['memory_info'].rss / (1024 * 1024)  # Convert to MB
                
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory_mb': mem_mb,
                    'cpu_percent': info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage (highest first)
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return processes
    
    def get_top_processes(self, count=10):
        """Get top N processes by RAM usage."""
        all_procs = self.get_all_processes()
        return all_procs[:count]
    
    def get_ram_hogs(self):
        """Get processes using more than threshold."""
        all_procs = self.get_all_processes()
        return [p for p in all_procs if p['memory_mb'] > self.threshold_mb]
    
    def get_system_stats(self):
        """Get overall system RAM statistics."""
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'used_gb': mem.used / (1024**3),
            'available_gb': mem.available / (1024**3),
            'percent': mem.percent,
            'cpu_percent': psutil.cpu_percent(interval=0.1)
        }
    
    def kill_process(self, pid):
        """Safely terminate a process by PID."""
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc.terminate()
            logger.info(f"Terminated process: {proc_name} (PID: {pid})")
            return True
        except psutil.NoSuchProcess:
            logger.error(f"Process {pid} not found")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied to terminate PID {pid}")
            return False
    
    def generate_report(self):
        """Generate a RAM usage report."""
        stats = self.get_system_stats()
        top_procs = self.get_top_processes(15)
        
        report = []
        report.append("=" * 60)
        report.append("RAM SENTINEL - PROCESS MONITOR REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("SYSTEM RAM USAGE:")
        report.append(f"  Total:     {stats['total_gb']:.2f} GB")
        report.append(f"  Used:      {stats['used_gb']:.2f} GB ({stats['percent']:.1f}%)")
        report.append(f"  Available: {stats['available_gb']:.2f} GB")
        report.append("")
        
        report.append("TOP 15 PROCESSES BY RAM USAGE:")
        report.append(f"{'PID':<8} {'Memory (MB)':<12} {'CPU %':<8} {'Name':<30}")
        report.append("-" * 60)
        
        for proc in top_procs:
            report.append(
                f"{proc['pid']:<8} {proc['memory_mb']:<12.1f} "
                f"{proc['cpu_percent']:<8.1f} {proc['name']:<30}"
            )
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def save_report(self, filepath):
        """Save report to file."""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {filepath}")
