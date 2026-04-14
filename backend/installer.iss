; ============================================================
; Crazy Lister v3.0 — Inno Setup Installer Script
; Download: https://jrsoftware.org/isdl.php#stable
; ============================================================
; Usage:
;   1. Install Inno Setup 6
;   2. Open this file in Inno Setup Compiler
;   3. Click "Build" → Creates installer .exe
; ============================================================

#define MyAppName "Crazy Lister"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "Crazy Lister"
#define MyAppURL "https://github.com/Amounir930/mazon"
#define MyAppExeName "CrazyLister.exe"
#define MyAppAssocName "Crazy Lister Project File"
#define MyAppAssocExt ".clp"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A8F7E9C2-4B3D-4E1F-9A5C-7D8E6F2B1A0C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=..\releases
OutputBaseFilename=CrazyLister-v{#MyAppVersion}-Setup
SetupIconFile=..\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable and all dependencies
Source: "..\backend\dist\CrazyLister\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Check if .NET is installed (required for pywebview)
  // Windows 10/11 has it by default, so we skip the check
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    // Show custom message after installation
    MsgBox('Crazy Lister v3.0 installed successfully!' #13#10#13#10 +
           'To get started:' #13#10 +
           '1. Launch Crazy Lister from the desktop shortcut' #13#10 +
           '2. Configure your Amazon SP-API credentials' #13#10 +
           '3. Start listing products!', mbInformation, MB_OK);
  end;
end;
