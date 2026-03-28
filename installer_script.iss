; ============================================================================
;  installer_script.iss — Inno Setup Script for Chinese Translator
;  Compile with Inno Setup 6.x: https://jrsoftware.org/isinfo.php
;  Prerequisites: Run `python build_exe.py` first to produce dist\ChineseTranslator.exe
; ============================================================================

#define MyAppName      "Chinese Translator"
#define MyAppVersion   "2.0"
#define MyAppPublisher "hungbbdzz"
#define MyAppURL       "https://github.com/hungbbdzz/ChineseTranslator"
#define MyAppExeName   "ChineseTranslator.exe"

[Setup]
AppId={{B7E2F4A1-3C9D-4F8E-A012-1D5E6F789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=ChineseTranslator_v{#MyAppVersion}_Setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
ShowLanguageDialog=no
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCompany={#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";          GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";    Description: "Launch automatically at &Windows startup"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Main executable — build with `python build_exe.py` first
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Bundled data (only needed if NOT packed inside the EXE via --add-data)
; Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
; Desktop (optional task)
Name: "{autodesktop}\{#MyAppName}";      Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Startup entry (optional task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
  ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Offer to launch app after install
Filename: "{app}\{#MyAppExeName}"; \
  Description: "Launch {#MyAppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user config on uninstall (optional — comment out to preserve user data)
; Type: files; Name: "{app}\config.json"
; Type: files; Name: "{app}\translation_history.json"
