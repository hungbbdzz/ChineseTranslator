Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where the script is located
strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Change working directory to script directory
WshShell.CurrentDirectory = strScriptDir

' Run the Python script with pythonw (no console)
' 0 = Hide window, False = Don't wait for completion
' --hidden: Start minimized to system tray
WshShell.Run """C:\Users\hunga\AppData\Local\Programs\Python\Python312\pythonw.exe"" ChineseTranslator.py --hidden", 0, False

Set WshShell = Nothing
Set fso = Nothing
