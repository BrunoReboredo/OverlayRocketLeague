@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0Piruleta - Overlay.exe" (
  start "PIRULETA - Overlay" "%~dp0Piruleta - Overlay.exe"
  exit /b 0
)
echo No se encuentra Piruleta - Overlay.exe junto al launcher.
pause
exit /b 1
