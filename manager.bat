@echo off
title Winter Arc - Protocol Manager
chcp 65001 >nul
cd /d "%~dp0"
echo [WINTER ARC] Starting Protocol Manager...

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else if exist "C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe" (
    set "PY_EXE=C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

"%PY_EXE%" manager_app.py
if %errorlevel% neq 0 (
    pause
)
