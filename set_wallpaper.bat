@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else if exist "C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe" (
    set "PY_EXE=C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

"%PY_EXE%" set_wallpaper.py
pause
