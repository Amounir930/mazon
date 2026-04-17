' CrazyLister v3.0 - Silent Launcher
' Double-click to start the app with NO console window

Dim shell, fso, projectDir, backendDir, cmd

Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")

' Get the folder where this VBS file is located
projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
backendDir = projectDir & "\backend"

' Check backend folder exists
If Not fso.FolderExists(backendDir) Then
    MsgBox "خطأ: مجلد backend غير موجود!" & vbCrLf & _
           "Error: backend folder not found!" & vbCrLf & _
           "Path: " & backendDir, vbCritical, "Crazy Lister"
    WScript.Quit 1
End If

' Kill any old pythonw process (to free port 8765)
shell.Run "cmd /c taskkill /F /IM pythonw.exe >nul 2>&1", 0, True
WScript.Sleep 1500

' Launch app silently (0 = hidden, False = don't wait)
shell.CurrentDirectory = backendDir
cmd = "pythonw -m app.launcher"
shell.Run cmd, 0, False

Set shell = Nothing
Set fso   = Nothing
