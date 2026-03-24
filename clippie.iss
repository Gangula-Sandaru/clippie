#define MyAppName "Clippie"
#define MyAppVersion "1.1"
#define MyAppPublisher "Clippie By Gangula"
#define MyAppExeName "Clippie.exe"

[Setup]
AppId={{DFD59DB1-D8DC-4BFB-99D7-D7AA4A157708}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
; Relative paths are mandatory for GitHub Actions
LicenseFile=LICENSE.txt
SetupIconFile=assets\icon.ico
OutputDir=dist
OutputBaseFilename=clippie-setup
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; This points to the folder created by PyInstaller --onedir --name "Clippie"
Source: "dist\Clippie\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Clippie\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
