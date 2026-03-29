"""
Dashboard Launcher for RAM Sentinel
Run this to start the web dashboard.
"""
import sys
import os
import webbrowser
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ram_sentinel.dashboard.server import run_server

def open_browser():
    """Open browser after server starts."""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == "__main__":
    print("🛡️  RAM Sentinel Dashboard")
    print("=" * 50)
    print("Starting server on http://127.0.0.1:5000")
    print("Opening browser...")
    print("\n[TIP] To open this again later, just run 'start_dashboard.bat'")
    print("[TIP] This app runs LOCALLY. It works without Internet.")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run server
    run_server()
