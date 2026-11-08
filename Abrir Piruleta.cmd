@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0app.py" (
  echo No se encuentra app.py en la carpeta de Piruleta - Overlay.
  pause
  exit /b 1
)
where pythonw.exe >nul 2>&1
if not errorlevel 1 (
  start "" pythonw.exe -B "%~dp0app.py"
  exit /b 0
)
where py.exe >nul 2>&1
if not errorlevel 1 (
  py.exe -3 -B "%~dp0app.py"
  if not errorlevel 1 exit /b 0
)
echo No se pudo abrir Piruleta - Overlay. Instala Python 3.11 o posterior con Tkinter.
pause
exit /b 1
