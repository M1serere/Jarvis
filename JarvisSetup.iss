#define MyAppName "Jarvis"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "Jarvis"
#define MyAppExeName "Jarvis.exe"
#define MyAppSourceDir "dist\\Jarvis"
#define MyBuildAssetsDir "build_assets"
#define MyInstallerName "JarvisSetup_" + MyAppVersion

[Setup]
AppId={{E33E27E2-9E9E-4B67-8B65-B7F8B8F2599A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir={#SourcePath}\installer\Output
OutputBaseFilename={#MyInstallerName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile={#MyBuildAssetsDir}\wizard.bmp
WizardSmallImageFile={#MyBuildAssetsDir}\wizard-small.bmp
SetupIconFile={#MyBuildAssetsDir}\jarvis.ico
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
CloseApplications=yes
CloseApplicationsFilter=Jarvis.exe
RestartApplications=no
UsePreviousAppDir=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Files]
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent
