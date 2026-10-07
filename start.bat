@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Winter Arc Command Center
cd /d "%~dp0"
echo ========================================================
echo   WINTER ARC COMMAND CENTER - DESKTOP WIDGET
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else if exist "C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe" (
    set "PY_EXE=C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

"%PY_EXE%" main.py
if %errorlevel% neq 0 (
  echo.
  echo [ERROR] An error occurred while running Winter Arc.
  echo If dependencies are missing, please run: pip install -r requirements.txt
  pause
)
