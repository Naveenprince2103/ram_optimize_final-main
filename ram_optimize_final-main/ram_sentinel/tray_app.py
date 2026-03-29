"""
System Tray Application for RAM Sentinel
Provides background service with system tray icon for easy control.
"""
import threading
import time
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
from ..core.logger import logger, console
from ..optimizer.tab_purger import TabPurger
from ..vault.manager import get_vault
from ..core.config import settings
from ..core.process_monitor import ProcessMonitor
from pathlib import Path

class RAMSentinelTray:
    def __init__(self):
        self.icon = None
        self.purger = None
        self.purger_thread = None
        self.purger_running = False
        self.vault = get_vault()
        self.vault_mounted = False
        self.process_monitor = ProcessMonitor()

class RAMSentinelTray:
    def __init__(self):
        self.icon = None
        self.purger = None
        self.purger_thread = None
        self.purger_running = False
        self.vault = get_vault()
        self.vault_mounted = False
        
    def create_icon_image(self, color="green"):
        """Create a simple icon image."""
        # Create a 64x64 image
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a circle
        if color == "green":
            fill_color = (0, 200, 0)
        elif color == "red":
            fill_color = (200, 0, 0)
        elif color == "yellow":
            fill_color = (200, 200, 0)
        else:
            fill_color = (128, 128, 128)
            
        draw.ellipse([10, 10, 54, 54], fill=fill_color, outline='black')
        
        # Draw "RS" text
        draw.text((20, 22), "RS", fill='white')
        
        return img
    
    def start_optimizer(self, icon, item):
        """Start the tab optimizer in background."""
        if self.purger_running:
            logger.warning("Optimizer already running")
            return
            
        def run_purger():
            try:
                self.purger = TabPurger()
                self.purger.start_session(headless=True)
                self.purger_running = True
                logger.info("Tab Optimizer started")
                
                while self.purger_running:
                    self.purger.scan_and_purge(dry_run=False)
                    time.sleep(60)  # Scan every 60 seconds
                    
            except Exception as e:
                logger.error(f"Optimizer error: {e}")
                self.purger_running = False
        
        self.purger_thread = threading.Thread(target=run_purger, daemon=True)
        self.purger_thread.start()
        self.update_icon("green")
    
    def stop_optimizer(self, icon, item):
        """Stop the tab optimizer."""
        if not self.purger_running:
            logger.warning("Optimizer not running")
            return
            
        self.purger_running = False
        if self.purger:
            self.purger.stop_session()
        logger.info("Tab Optimizer stopped")
        self.update_icon("gray")
    
    def mount_vault(self, icon, item):
        """Mount the Ghost Drive."""
        try:
            mount_point = settings.DEFAULT_MOUNT_POINT_WIN
            size = settings.DEFAULT_VAULT_SIZE
            success = self.vault.mount(size, mount_point)
            if success:
                self.vault_mounted = True
                logger.info(f"Vault mounted at {mount_point}")
            else:
                logger.error("Failed to mount vault")
        except Exception as e:
            logger.error(f"Vault mount error: {e}")
    
    def unmount_vault(self, icon, item):
        """Unmount the Ghost Drive."""
        try:
            mount_point = settings.DEFAULT_MOUNT_POINT_WIN
            success = self.vault.unmount(mount_point)
            if success:
                self.vault_mounted = False
                logger.info("Vault unmounted")
            else:
                logger.error("Failed to unmount vault")
        except Exception as e:
            logger.error(f"Vault unmount error: {e}")
    
    def panic(self, icon, item):
        """Emergency panic - stop everything and wipe."""
        logger.warning("PANIC INITIATED!")
        
        # Stop optimizer
        if self.purger_running:
            self.stop_optimizer(icon, item)
        
        # Close all tabs if purger exists
        if self.purger and self.purger.context:
            for page in self.purger.context.pages:
                try:
                    page.close()
                except:
                    pass
        
        # Destroy vault
        try:
            self.vault.panic()
        except Exception as e:
            logger.error(f"Vault panic error: {e}")
        
        logger.warning("Panic complete")
    
    def show_process_monitor(self, icon, item):
        """Show top RAM-consuming processes."""
        top_procs = self.process_monitor.get_top_processes(10)
        stats = self.process_monitor.get_system_stats()
        
        console.print("\n[bold cyan]RAM USAGE MONITOR[/bold cyan]")
        console.print(f"System RAM: {stats['used_gb']:.1f}GB / {stats['total_gb']:.1f}GB ({stats['percent']:.1f}%)")
        console.print("\n[bold]Top 10 Processes:[/bold]")
        console.print(f"{'PID':<8} {'Memory (MB)':<12} {'Name':<30}")
        console.print("-" * 50)
        
        for proc in top_procs:
            console.print(f"{proc['pid']:<8} {proc['memory_mb']:<12.1f} {proc['name']:<30}")
    
    def generate_ram_report(self, icon, item):
        """Generate and save RAM usage report."""
        report_dir = Path.home() / "Documents" / "RAM_Sentinel_Reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        filename = f"ram_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = report_dir / filename
        
        self.process_monitor.save_report(str(filepath))
        console.print(f"\n[green]✅ Report saved to:[/green] {filepath}")
    
    def show_status(self, icon, item):
        """Show current status."""
        status = []
        status.append("RAM Sentinel Status:")
        status.append(f"  Optimizer: {'Running' if self.purger_running else 'Stopped'}")
        status.append(f"  Vault: {'Mounted' if self.vault_mounted else 'Not Mounted'}")
        
        console.print("\n".join(status))
    
    def update_icon(self, color):
        """Update the tray icon color."""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)
    
    def quit_app(self, icon, item):
        """Quit the application."""
        if self.purger_running:
            self.stop_optimizer(icon, item)
        icon.stop()
    
    def run(self):
        """Run the system tray application."""
        # Create menu
        menu = pystray.Menu(
            item('Start Optimizer', self.start_optimizer),
            item('Stop Optimizer', self.stop_optimizer),
            pystray.Menu.SEPARATOR,
            item('Mount Vault', self.mount_vault),
            item('Unmount Vault', self.unmount_vault),
            pystray.Menu.SEPARATOR,
            item('📊 Process Monitor', self.show_process_monitor),
            item('📄 Generate RAM Report', self.generate_ram_report),
            pystray.Menu.SEPARATOR,
            item('🚨 PANIC', self.panic),
            pystray.Menu.SEPARATOR,
            item('Status', self.show_status),
            item('Quit', self.quit_app)
        )
        
        # Create icon
        self.icon = pystray.Icon(
            "ram_sentinel",
            self.create_icon_image("gray"),
            "RAM Sentinel",
            menu
        )
        
        logger.info("RAM Sentinel Tray started")
        self.icon.run()

def main():
    app = RAMSentinelTray()
    app.run()

if __name__ == "__main__":
    main()
