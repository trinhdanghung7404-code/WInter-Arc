Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir

PyExe = "pythonw.exe"
If FSO.FileExists(ScriptDir & "\.venv\Scripts\pythonw.exe") Then
    PyExe = ScriptDir & "\.venv\Scripts\pythonw.exe"
ElseIf FSO.FileExists(ScriptDir & "\venv\Scripts\pythonw.exe") Then
    PyExe = ScriptDir & "\venv\Scripts\pythonw.exe"
ElseIf FSO.FileExists("C:\Users\Admin\Documents\Module4-main\.venv\Scripts\pythonw.exe") Then
    PyExe = "C:\Users\Admin\Documents\Module4-main\.venv\Scripts\pythonw.exe"
End If

WshShell.Run """" & PyExe & """ """ & ScriptDir & "\main.py""", 0, False