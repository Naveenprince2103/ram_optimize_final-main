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
    taskkill /IM chrome.exe /F 2>nul
    timeout /t 1 >nul
    start chrome --remote-debugging-port=9222 --restore-last-session
)

python start_dashboard.py
pause
