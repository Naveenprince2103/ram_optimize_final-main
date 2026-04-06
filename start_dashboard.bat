@echo off
REM RAM Sentinel Dashboard Launcher
REM Elevate to Admin
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

REM Open Chrome with debug port 9222 so Optimizer can attach automatically
netstat -ano | find "9222" >nul
if '%errorlevel%' NEQ '0' (
    echo [SENTINEL] Port 9222 is closed. Restarting Chrome with Debug mode...
    taskkill /IM chrome.exe /F 2>nul
    taskkill /IM msedge.exe /F 2>nul
    timeout /t 2 >nul
    
    REM Try different Chrome locations with --user-data-dir to force port activation
    SET CHROME_FLAGS=--remote-debugging-port=9222 --restore-last-session --no-first-run
    
    if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
        start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" %CHROME_FLAGS%
    ) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" %CHROME_FLAGS%
    ) else (
        start chrome %CHROME_FLAGS%
    )
    
    echo [SENTINEL] Waiting for Chrome to initialize debug port...
    timeout /t 3 >nul
)

start "" python widget.py
python start_dashboard.py
pause
