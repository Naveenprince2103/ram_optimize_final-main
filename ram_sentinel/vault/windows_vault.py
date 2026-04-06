import subprocess
import os
from .base_vault import BaseVault
from ..core.logger import logger
from ..core.os_utils import is_admin

class WindowsVault(BaseVault):
    def __init__(self):
        self.vhd_path = "C:\\ram_sentinel_vault.vhd"
        self.script_path = "C:\\ram_sentinel_diskpart.txt"

    def mount(self, size: str, mount_point: str = "R:") -> bool:
        if not is_admin():
            logger.error("Admin privileges required to mount Ghost Drive.")
            return False
            
        # Clean up existing
        self.unmount(mount_point)

        # Convert size to MB (Diskpart likes MB)
        size_mb = 1024 # Default 1GB
        if 'G' in size.upper():
            size_mb = int(size.upper().replace('G', '')) * 1024
        elif 'M' in size.upper():
            size_mb = int(size.upper().replace('M', ''))

        # Create Diskpart script
        script_content = f"""
create vdisk file="{self.vhd_path}" maximum={size_mb} type=expandable
attach vdisk
create partition primary
format fs=ntfs quick label="GhostDrive"
assign letter={mount_point.replace(':', '')}
"""
        with open(self.script_path, 'w') as f:
            f.write(script_content)

        logger.info(f"Creating Virtual Ghost Drive ({size_mb}MB) at {mount_point}...")
        
        try:
            result = subprocess.run(["diskpart", "/s", self.script_path], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Diskpart failed: {result.stderr or result.stdout}")
                return False
            
            logger.info("Ghost Drive mounted and ready via Diskpart.")
            return True
        except Exception as e:
            logger.error(f"Mount error: {e}")
            return False
        finally:
            if os.path.exists(self.script_path):
                os.remove(self.script_path)

    def unmount(self, mount_point: str = "R:") -> bool:
        script_content = f"""
select vdisk file="{self.vhd_path}"
detach vdisk
"""
        with open(self.script_path, 'w') as f:
            f.write(script_content)
            
        try:
            subprocess.run(["diskpart", "/s", self.script_path], capture_output=True, text=True)
            if os.path.exists(self.vhd_path):
                os.remove(self.vhd_path)
            return True
        except:
            return False
        finally:
            if os.path.exists(self.script_path):
                os.remove(self.script_path)

    def panic(self) -> bool:
        logger.warning("PANIC! Detaching and deleting Vault...")
        return self.unmount()
