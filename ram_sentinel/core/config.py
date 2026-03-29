import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    # Optimizer Settings
    MAX_TAB_AGE_MINUTES: int = 60
    INACTIVE_THRESHOLD_MINUTES: int = 30
    READ_LATER_DIR: str = str(Path.home() / "Documents" / "RAM_Sentinel_ReadLater")
    
    # Vault Settings
    DEFAULT_VAULT_SIZE: str = "500M"
    DEFAULT_MOUNT_POINT_WIN: str = "R:"
    DEFAULT_MOUNT_POINT_UNIX: str = "/mnt/ram_vault"
    
    # System
    DEBUG_MODE: bool = False

    def __post_init__(self):
        os.makedirs(self.READ_LATER_DIR, exist_ok=True)

# Global config instance
settings = Config()
