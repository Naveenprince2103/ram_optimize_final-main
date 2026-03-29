@echo off
REM Mount Ghost Drive (Auto-requests Admin)
REM This will ask for admin permission automatically

cd /d "%~dp0"

echo ========================================
echo RAM Sentinel - Mount Ghost Drive
echo ========================================
echo.
echo Requesting Administrator privileges...
echo.

python -m ram_sentinel vault --mount --size 500M --mount-point R:

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! Drive R: is now mounted
    echo ========================================
    echo.
    echo You can now use R: drive in File Explorer
    echo Data will be lost on unmount or shutdown
    echo.
) else (
    echo.
    echo ERROR: Failed to mount drive
    echo Make sure you clicked "Yes" for admin privileges
    echo.
)

pause
