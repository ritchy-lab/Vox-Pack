; ============================================================
; Vox-Pack — installeur Windows (Inno Setup 6)
; ------------------------------------------------------------
; Emballage du dossier onedir produit par PyInstaller :
;
;     python -m PyInstaller Vox-Pack.spec --noconfirm
;     ISCC.exe /DMyAppVersion=2.0.0 installer\Vox-Pack.iss
;
; Installation par utilisateur, sans droits administrateur :
;   %LOCALAPPDATA%\Programs\Vox-Pack
; Les listes et réglages restent dans Documents\Vox-Pack : la
; désinstallation ne les touche pas.
; ============================================================

#define MyAppName "Vox-Pack"
#ifndef MyAppVersion
  #define MyAppVersion "2.0.0"
#endif
#define MyAppPublisher "ritchy-lab"
#define MyAppURL "https://ritchy-lab.github.io/Vox-Pack/"
#define MyAppExeName "Vox-Pack.exe"
#define MyAppId "{{BA0EBEC5-825F-454B-AE50-DB72C54D1CDC}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://github.com/ritchy-lab/Vox-Pack/issues
AppUpdatesURL=https://github.com/ritchy-lab/Vox-Pack/releases
AppCopyright=© 2026 ritchy-lab
AppComments=Fait parler ta radiocommande.
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} {#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoTextVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Vox-Pack-Setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
MinVersion=10.0
CloseApplications=yes
RestartApplications=no
LicenseFile=..\LICENSE

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Vox-Pack\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
