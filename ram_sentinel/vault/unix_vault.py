import subprocess
import os
from .base_vault import BaseVault
from ..core.logger import logger
from ..core.os_utils import is_admin

class UnixVault(BaseVault):
    def mount(self, size: str, mount_point: str) -> bool:
        if not is_admin():
            logger.error("Root privileges required to mount tmpfs.")
            return False

        if not os.path.exists(mount_point):
            os.makedirs(mount_point, exist_ok=True)

        # mount -t tmpfs -o size=512m tmpfs /mnt/ram
        cmd = ["mount", "-t", "tmpfs", "-o", f"size={size}", "tmpfs", mount_point]
        logger.info(f"Mounting Unix Vault ({size}) at {mount_point}...")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Vault mounted successfully.")
            return True
        else:
            logger.error(f"Failed to mount: {result.stderr}")
            return False

    def unmount(self, mount_point: str) -> bool:
        if not is_admin():
            logger.error("Root privileges required to unmount.")
            return False

        cmd = ["umount", mount_point]
        logger.info(f"Unmounting Vault at {mount_point}...")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Vault unmounted.")
            return True
        else:
            logger.error(f"Failed to unmount: {result.stderr}")
            return False

    def panic(self) -> bool:
        # Implemented for completeness, but requires known mount point management
        # For this prototype we'd need to store the active mount point.
        # Assuming CLI passes it or config has default.
        return False
