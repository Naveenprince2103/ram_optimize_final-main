@echo off
REM Unmount Ghost Drive (Auto-requests Admin)
REM This will ask for admin permission automatically

cd /d "%~dp0"

echo ========================================
echo RAM Sentinel - Unmount Ghost Drive
echo ========================================
echo.
echo WARNING: All data on R: will be permanently deleted!
echo.
pause
echo.
echo Requesting Administrator privileges...
echo.

python -m ram_sentinel vault --unmount --mount-point R:

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! Drive R: has been unmounted
    echo ========================================
    echo.
    echo All data has been permanently deleted
    echo RAM has been freed
    echo.
) else (
    echo.
    echo ERROR: Failed to unmount drive
    echo Make sure you clicked "Yes" for admin privileges
    echo.
)

pause
