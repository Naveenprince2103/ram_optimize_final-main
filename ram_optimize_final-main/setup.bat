@echo off
REM RAM Sentinel - Quick Setup Script for New Computers
REM Run this after copying RAM Sentinel to a new computer

echo ========================================
echo RAM Sentinel - Quick Setup
echo ========================================
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Make sure Python is installed and added to PATH
    pause
    exit /b 1
)

echo.
echo Step 2: Installing Playwright browsers...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Playwright browsers
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run RAM Sentinel:
echo   - Dashboard:  start_dashboard.bat
echo   - Tray App:   start_ram_sentinel.bat
echo   - CLI:        python -m ram_sentinel optimize --auto
echo.
echo Optional: Install ImDisk Toolkit for Ghost Drive
echo Download from: https://sourceforge.net/projects/imdisk-toolkit/
echo.
pause
