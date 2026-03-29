"""
Setup Auto-Start for RAM Sentinel
Adds RAM Sentinel to Windows Startup folder so it runs automatically on boot.
"""
import os
import shutil
import sys
from pathlib import Path

def setup_autostart():
    """Add RAM Sentinel to Windows Startup."""
    # Resolve APPDATA with a safe fallback
    appdata = os.getenv('APPDATA')
    if not appdata and os.name == 'nt':
        # Try expected location under user profile
        home = Path.home()
        candidate = home / 'AppData' / 'Roaming'
        if candidate.exists():
            appdata = str(candidate)

    if not appdata:
        print("Error: APPDATA not found. This script is for Windows only.")
        return False

    # Get startup folder path
    startup_folder = Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    # Ensure startup folder exists
    try:
        startup_folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If we cannot create the folder, continue and let copy fail with clear message
        pass

    # Get current script directory and batch file path
    current_dir = Path(__file__).parent.absolute()
    bat_file = current_dir / 'start_ram_sentinel.bat'

    if not bat_file.exists():
        print(f"Error: {bat_file} not found!")
        return False

    # Create shortcut path in startup folder
    shortcut_path = startup_folder / 'RAM Sentinel.bat'

    try:
        # If target exists, attempt to replace it
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
            except Exception:
                # If we can't remove it, attempt to overwrite via copy
                pass

        shutil.copy2(str(bat_file), str(shortcut_path))
        print("✅ RAM Sentinel added to startup!")
        print("   Location:", shortcut_path)
        print("\nRAM Sentinel will now start automatically when Windows boots.")
        return True
    except PermissionError as e:
        print(f"❌ Permission error: {e}")
        print("Try running this script as an administrator or manually copy the batch file.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nManual setup:")
        print("1. Copy:", bat_file)
        print("2. To:", startup_folder)
        return False

def remove_autostart():
    """Remove RAM Sentinel from Windows Startup."""
    appdata = os.getenv('APPDATA')
    if not appdata and os.name == 'nt':
        home = Path.home()
        candidate = home / 'AppData' / 'Roaming'
        if candidate.exists():
            appdata = str(candidate)

    if not appdata:
        print("Error: APPDATA not found. This script is for Windows only.")
        return False

    startup_folder = Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    shortcut_path = startup_folder / 'RAM Sentinel.bat'

    try:
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
                print("✅ RAM Sentinel removed from startup")
            except PermissionError:
                print("❌ Permission denied while removing startup shortcut. Run as administrator.")
                return False
        else:
            print("ℹ️  RAM Sentinel is not in startup")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("RAM Sentinel Auto-Start Setup")
    print("=" * 40)
    print("\n1. Enable auto-start")
    print("2. Disable auto-start")
    print("3. Exit")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        setup_autostart()
    elif choice == "2":
        remove_autostart()
    else:
        print("Cancelled")
