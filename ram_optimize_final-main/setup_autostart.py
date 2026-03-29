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
    # Get startup folder path
    startup_folder = Path(os.getenv('APPDATA')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    
    # Get current script directory
    current_dir = Path(__file__).parent.absolute()
    bat_file = current_dir / 'start_ram_sentinel.bat'
    
    if not bat_file.exists():
        print(f"Error: {bat_file} not found!")
        return False
    
    # Create shortcut in startup folder
    shortcut_path = startup_folder / 'RAM Sentinel.bat'
    
    try:
        # Copy the batch file to startup folder
        shutil.copy(bat_file, shortcut_path)
        print(f"✅ RAM Sentinel added to startup!")
        print(f"   Location: {shortcut_path}")
        print(f"\nRAM Sentinel will now start automatically when Windows boots.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nManual setup:")
        print(f"1. Copy: {bat_file}")
        print(f"2. To: {startup_folder}")
        return False

def remove_autostart():
    """Remove RAM Sentinel from Windows Startup."""
    startup_folder = Path(os.getenv('APPDATA')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    shortcut_path = startup_folder / 'RAM Sentinel.bat'
    
    try:
        if shortcut_path.exists():
            shortcut_path.unlink()
            print("✅ RAM Sentinel removed from startup")
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
