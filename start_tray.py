"""
Launcher script for RAM Sentinel Tray Application
Run this to start RAM Sentinel in the system tray.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ram_sentinel.tray_app import main

if __name__ == "__main__":
    main()
