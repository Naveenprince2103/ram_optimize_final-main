from ..core.os_utils import get_os_type
from .windows_vault import WindowsVault
from .unix_vault import UnixVault
from .base_vault import BaseVault

def get_vault() -> BaseVault:
    os_type = get_os_type()
    if os_type == 'windows':
        return WindowsVault()
    elif os_type in ['linux', 'darwin']:
        return UnixVault()
    else:
        raise NotImplementedError(f"OS {os_type} not supported for Vault.")
