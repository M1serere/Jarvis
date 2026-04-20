#define MyAppName "Jarvis"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jarvis"
#define MyAppExeName "Jarvis.exe"
#define MyAppSourceDir "dist\\Jarvis"
#define MyBuildAssetsDir "build_assets"

[Setup]
AppId={{E33E27E2-9E9E-4B67-8B65-B7F8B8F2599A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=.
OutputBaseFilename=JarvisSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile={#MyBuildAssetsDir}\wizard.bmp
WizardSmallImageFile={#MyBuildAssetsDir}\wizard-small.bmp

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "uninstall_jarvis.ps1"; DestDir: "{app}"; Flags: ignoreversion
Source: "uninstall_jarvis.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\Удалить {#MyAppName}"; Filename: "{app}\uninstall_jarvis.bat"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent
