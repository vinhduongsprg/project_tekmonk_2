Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
venvPython = base & "\.venv\Scripts\python.exe"

If fso.FileExists(venvPython) Then
  shell.Run """" & venvPython & """ farmer_app\app.py", 0, False
Else
  shell.Run "python farmer_app\app.py", 0, False
End If
