@echo off
REM RAM Sentinel Tray Application Launcher
REM Double-click this file to start RAM Sentinel in the system tray

cd /d "%~dp0"
pythonw start_tray.py

REM Note: Using pythonw (not python) to run without console window
