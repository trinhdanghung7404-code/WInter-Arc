import os
import subprocess

vbs_code = '''
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\\Users\\Admin\\Documents\\Winter Arc"
WshShell.Run """C:\\Users\\Admin\\Documents\\Module4-main\\.venv\\Scripts\\pythonw.exe"" ""C:\\Users\\Admin\\Documents\\Winter Arc\\main.py""", 0, False
'''
with open(r"C:\Users\Admin\Documents\Winter Arc\start_silent.vbs", "w", encoding="utf-8") as f:
    f.write(vbs_code.strip())

stop_bat = '''@echo off
chcp 65001 >nul
echo Dang tat Winter Arc Widgets...
taskkill /F /IM pythonw.exe >nul 2>&1
echo Da dung tat ca tien trinh Winter Arc.
timeout /t 2 >nul
'''
with open(r"C:\Users\Admin\Documents\Winter Arc\stop.bat", "w", encoding="utf-8") as f:
    f.write(stop_bat)

def make_shortcut(lnk_path, target, args, work_dir, icon_path, description):
    ps_cmd = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{lnk_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Arguments = '{args}'
$Shortcut.WorkingDirectory = "{work_dir}"
$Shortcut.IconLocation = "{icon_path},0"
$Shortcut.Description = "{description}"
$Shortcut.Save()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
    print(f"Created shortcut: {lnk_path}")

desktop = os.path.expanduser(r"~\Desktop")
startup = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
app_dir = r"C:\Users\Admin\Documents\Winter Arc"
pythonw = r"C:\Users\Admin\Documents\Module4-main\.venv\Scripts\pythonw.exe"
icon = os.path.join(app_dir, "app_icon.ico")
main_script = os.path.join(app_dir, "main.py")
manager_script = os.path.join(app_dir, "manager_app.py")

# 1. Desktop shortcut for main widget
make_shortcut(
    os.path.join(desktop, "Winter Arc.lnk"),
    pythonw,
    f'"{main_script}"',
    app_dir,
    icon,
    "Winter Arc Apple Desktop Widgets"
)

# 2. Desktop shortcut for Protocol Manager
make_shortcut(
    os.path.join(desktop, "Winter Arc Manager.lnk"),
    pythonw,
    f'"{manager_script}"',
    app_dir,
    icon,
    "Quản lý mục tiêu Winter Arc"
)

# 3. Startup folder shortcut (Chay ngam cung Windows)
make_shortcut(
    os.path.join(startup, "Winter Arc.lnk"),
    pythonw,
    f'"{main_script}"',
    app_dir,
    icon,
    "Winter Arc Auto-Start"
)

# 4. Stop shortcut
make_shortcut(
    os.path.join(desktop, "Stop Winter Arc.lnk"),
    os.path.join(app_dir, "stop.bat"),
    "",
    app_dir,
    icon,
    "Dừng Winter Arc Widgets"
)

print("All shortcuts created successfully!")
