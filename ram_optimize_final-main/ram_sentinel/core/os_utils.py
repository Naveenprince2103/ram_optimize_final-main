import sys
import os
import ctypes
import platform

def get_os_type() -> str:
    """Returns 'windows', 'linux', or 'darwin'."""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'darwin'
    return 'unknown'

def is_admin() -> bool:
    """Check if the script is running with administrative privileges."""
    os_type = get_os_type()
    try:
        if os_type == 'windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False
