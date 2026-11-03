@echo off
cd /d "%~dp0"
pythonw app.py
if errorlevel 1 (
  echo No se pudo abrir Piruleta / Overlay. Se necesita Python 3.11 o posterior con Tkinter.
  pause
)
