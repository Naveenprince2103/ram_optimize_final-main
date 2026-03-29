import subprocess
import shutil
import os
from .base_vault import BaseVault
from ..core.logger import logger
from ..core.os_utils import is_admin

class WindowsVault(BaseVault):
    def mount(self, size: str, mount_point: str = "R:") -> bool:
        if not is_admin():
            logger.error("Admin privileges required to mount ImDisk.")
            return False
            
        # Parse size (e.g. 500M -> 500M)
        # ImDisk expects -s size (e.g. 500M) -m mountpoint
        
        # Clean up any existing mount first
        self.unmount(mount_point)

        # 1. Create the device (raw)
        cmd_create = ["imdisk", "-a", "-s", size, "-m", mount_point]
        logger.info(f"Creating RAM Disk ({size}) at {mount_point}...")
        
        try:
            result = subprocess.run(cmd_create, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to create RAM disk: {result.stderr or result.stdout}")
                return False
                
            # 2. Format it (NTFS) - This is more reliable done separately
            logger.info("Formatting drive...")
            # We use echo Y | format ... to bypass confirmation
            cmd_format = f"echo Y | format {mount_point} /FS:NTFS /Q /V:GhostDrive"
            
            # Use shell=True for piping echo
            fmt_result = subprocess.run(cmd_format, shell=True, capture_output=True, text=True)
            
            if fmt_result.returncode != 0:
                logger.error(f"Failed to format: {fmt_result.stderr or fmt_result.stdout}")
                # Cleanup if format fails
                self.unmount(mount_point)
                return False
                
            logger.info("Vault mounted and ready.")
            return True
            
        except FileNotFoundError:
            logger.error("ImDisk executable not found in PATH. Please install ImDisk Toolkit.")
            return False

    def unmount(self, mount_point: str = "R:") -> bool:
        if not is_admin():
            logger.error("Admin privileges required to unmount.")
            return False

        # Forced unmount: imdisk -D -m R:
        cmd = ["imdisk", "-D", "-m", mount_point]
        logger.info(f"Unmounting Vault at {mount_point}...")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Vault unmounted.")
            return True
        else:
            logger.error(f"Failed to unmount: {result.stderr}")
            return False

    def panic(self) -> bool:
        """
        Panic Wipe:
        1. Overwrite files? (Too slow for panic)
        2. Force unmount immediately.
        """
        logger.warning("PANIC INITIATED! Destroying Vault...")
        # We can try to format it first to 'wipe' FS table?
        # Faster to just detach. RAM is volatile, content is gone on power loss.
        # But to be safe, we detach.
        return self.unmount()
