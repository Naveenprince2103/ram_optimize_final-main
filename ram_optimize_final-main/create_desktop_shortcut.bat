@echo off
echo Creating Desktop Shortcut...
set "target=%~dp0start_dashboard.bat"
set "shortcut=%UserProfile%\Desktop\RAM Sentinel Dashboard.lnk"
set "workdir=%~dp0"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%shortcut%'); $s.TargetPath = '%target%'; $s.WorkingDirectory = '%workdir%'; $s.IconLocation = 'shell32.dll,300'; $s.Save()"

echo.
echo Shortcut created! Look for "RAM Sentinel Dashboard" on your desktop.
echo.
pause
