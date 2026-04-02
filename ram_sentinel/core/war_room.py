import psutil
import subprocess
import time
import ctypes
import logging

class WarRoomManager:
    def __init__(self):
        self.game_mode_active = False
        
        # Windows services that are completely safe to temporarily pause 
        # while gaming to free up CPU cycles and RAM.
        self.non_essential_services = [
            "Spooler",      # Print Spooler
            "WSearch",      # Windows Search (Disk indexing)
            "SysMain",      # Superfetch
            "wuauserv",     # Windows Update
            "Bits",         # Background Intelligent Transfer Service
            "DiagTrack"     # Connected User Experiences and Telemetry
        ]
        
        # We remember which processes we de-prioritized so we can restore them later
        self.modified_processes = []

    def toggle_game_mode(self, target_game_exe=None):
        """Toggles the War Room state"""
        if self.game_mode_active:
            return self._disable_game_mode()
        else:
            return self._enable_game_mode(target_game_exe)

    def _enable_game_mode(self, target_game_exe=None):
        """Engage maximum system performance"""
        self.game_mode_active = True
        log_msgs = []
        
        log_msgs.append("🎮 ENGAGING WAR ROOM MODE...")
        
        # 1. Stop background services
        for svc in self.non_essential_services:
            try:
                # Use subprocess to stop the service (requires admin rights to succeed completely, 
                # but harmless if it fails without admin)
                subprocess.run(['sc', 'stop', svc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log_msgs.append(f"[+] Suspended Background Service: {svc}")
            except Exception:
                pass
                
        # 2. De-prioritize ALL non-essential background processes
        # Process priority classes in Windows
        IDLE_PRIORITY_CLASS = 0x00000040
        HIGH_PRIORITY_CLASS = 0x00000080
        
        important_system_apps = ['explorer.exe', 'csrss.exe', 'smss.exe', 'winlogon.exe', 'services.exe', 'lsass.exe']
        
        for p in psutil.process_iter(['name']):
            try:
                name = p.info['name'].lower()
                pid = p.pid
                
                # Protect system essentials
                if name in important_system_apps:
                    continue
                    
                proc = psutil.Process(pid)
                
                # If a target game was provided and this is it, BOOST it!
                if target_game_exe and name == target_game_exe.lower():
                    proc.nice(HIGH_PRIORITY_CLASS)
                    log_msgs.append(f"🚀 BOOSTED GAME PRIORITY: {target_game_exe}")
                    continue
                    
                # Otherwise, drop the priority of everything else!
                # We skip our own python script to not lag the dashboard
                if 'python' not in name:
                    # Save current priority to restore it later
                    current_nice = proc.nice()
                    self.modified_processes.append({'pid': pid, 'old_nice': current_nice})
                    
                    # Set to lowest priority to give the CPU to the game
                    proc.nice(IDLE_PRIORITY_CLASS)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        log_msgs.append("🛡️ All available system resources have been routed to foreground tasks.")
        return True, log_msgs

    def _disable_game_mode(self):
        """Restore normal system performance"""
        self.game_mode_active = False
        log_msgs = []
        
        log_msgs.append("🛑 DISENGAGING WAR ROOM MODE...")
        
        # 1. Restart background services
        for svc in self.non_essential_services:
            try:
                subprocess.run(['sc', 'start', svc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log_msgs.append(f"[-] Restored Background Service: {svc}")
            except Exception:
                pass
                
        # 2. Restore process priorities
        restored_count = 0
        for data in self.modified_processes:
            try:
                proc = psutil.Process(data['pid'])
                proc.nice(data['old_nice'])
                restored_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        self.modified_processes.clear()
        
        log_msgs.append(f"♻️ Restored priority for {restored_count} background tasks.")
        log_msgs.append("✅ System is back to normal everyday operation.")
        return False, log_msgs

war_room = WarRoomManager()
