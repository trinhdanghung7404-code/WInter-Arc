@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Winter Arc Command Center
cd /d "%~dp0"
echo ========================================================
echo   WINTER ARC COMMAND CENTER - KHOI DONG DESKTOP WIDGET
echo ========================================================
"C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe" main.py
if %errorlevel% neq 0 (
  echo.
  echo [LOI] Co loi xay ra khi khoi chay.
  pause
)
