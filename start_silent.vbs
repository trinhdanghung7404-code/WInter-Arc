Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Admin\Documents\Winter Arc"
WshShell.Run """C:\Users\Admin\Documents\Module4-main\.venv\Scripts\pythonw.exe"" ""C:\Users\Admin\Documents\Winter Arc\main.py""", 0, False