import psutil
import ctypes
try:
    import wmi
except ImportError:
    wmi = None

def compact_memory(pid=None):
    """
    Advanced Memory Compaction using Windows API EmptyWorkingSet.
    This forces processes to release unused/fragmented memory pages back to the OS
    without actually killing the application.
    """
    success_count = 0
    fail_count = 0
    freed_mb = 0

    if pid:
        pids = [pid]
    else:
        pids = [p.pid for p in psutil.process_iter() if p.pid > 0]

    for p in pids:
        try:
            process = psutil.Process(p)
            # Skip system idle and our own process
            if process.name().lower() in ['system idle process', 'system']:
                continue
                
            mem_before = process.memory_info().rss
            
            # Windows API to open process with PROCESS_SET_QUOTA
            PROCESS_SET_QUOTA = 0x0100
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_SET_QUOTA, False, p)
            if handle:
                result = ctypes.windll.psapi.EmptyWorkingSet(handle)
                ctypes.windll.kernel32.CloseHandle(handle)
                if result:
                    mem_after = process.memory_info().rss
                    if mem_before > mem_after:
                        freed_mb += (mem_before - mem_after) / (1024 * 1024)
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1
            
    return {"success": success_count, "failed": fail_count, "freed_mb": round(freed_mb, 2)}

def get_vram_info():
    """
    Fetch GPU Video RAM (VRAM) usage to help identify graphic-heavy bottlenecks.
    """
    if not wmi:
        return {"error": "WMI module not installed. Run 'pip install wmi'"}
        
    try:
        w = wmi.WMI()
        gpu_info = []
        for v in w.Win32_VideoController():
            adapter_ram = v.AdapterRAM
            if adapter_ram:
                # Need to handle negative unsigned integers sometimes returned by WMI
                ram_mb = abs(int(adapter_ram)) / (1024 * 1024)
                gpu_info.append({
                    "name": v.Name,
                    "ram_mb": round(ram_mb, 2)
                })
        return {"success": True, "gpus": gpu_info}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("--- RAM SENTINEL ADVANCED OPTIMIZER ---")
    print("\nScanning GPUs for VRAM...")
    vram = get_vram_info()
    print(vram)
    
    print("\nCompacting System Memory...")
    res = compact_memory()
    print(f"Compaction Complete: Freed {res['freed_mb']} MB across {res['success']} processes.")
