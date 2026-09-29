@echo off
title Winter Arc - Protocol Manager
chcp 65001 >nul
cd /d "%~dp0"
echo [WINTER ARC] Đang khởi động màn hình Quản lý mục tiêu (Protocol Manager)...
call "C:\Users\Admin\Documents\Module4-main\.venv\Scripts\python.exe" manager_app.py
pause
