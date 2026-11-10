@echo off
setlocal
rem Version actual: RCK ajustado a la referencia de video. Cierra la app anterior antes de abrir.
title Piruleta - Overlay 1.1.0
cd /d "%~dp0"
if not exist "%~dp0app.py" (
  echo No se encuentra app.py en la carpeta de Piruleta - Overlay.
  pause
  exit /b 1
)
if exist "C:\Python313\pythonw.exe" (
  start "Piruleta - Overlay" /wait "C:\Python313\pythonw.exe" -B -E "%~dp0app.py"
  if not errorlevel 1 exit /b 0
  goto error
)
where pythonw.exe >nul 2>&1
if not errorlevel 1 (
  start "Piruleta - Overlay" /wait pythonw.exe -B -E "%~dp0app.py"
  if not errorlevel 1 exit /b 0
  goto error
)
where py.exe >nul 2>&1
if not errorlevel 1 (
  py.exe -3 -B -E "%~dp0app.py"
  if not errorlevel 1 exit /b 0
)
:error
echo No se pudo abrir Piruleta - Overlay. Se necesita Python 3.11 o posterior con Tkinter.
echo Cierra la ventana anterior de la app antes de abrir la nueva version.
pause
exit /b 1
