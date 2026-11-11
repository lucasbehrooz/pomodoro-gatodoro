; Instalador do Pomodoro (Inno Setup 6).
;
; Uso (a partir da raiz do repositório, depois de gerar dist\PomodoroGatodoro.exe):
;   iscc /DMyAppVersion=0.0.3 packaging\pomodoro.iss
; Saída: dist\pomodoro-gatodoro-x64-setup.exe
;
; O Inno Setup resolve caminhos relativos a partir da pasta deste script,
; por isso ".." aponta para a raiz do repositório.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

#define MyAppName "Pomodoro Gatodoro"
#define MyAppExeName "PomodoroGatodoro.exe"
#define RepoRoot ".."

; Idioma português só se o compilador instalado tiver o arquivo; senão, inglês (padrão).
#if FileExists(GetEnv("ProgramFiles(x86)") + "\Inno Setup 6\Languages\BrazilianPortuguese.isl")
  #define HasPtBr
#endif

[Setup]
AppId={{75746350-CC48-423F-8FF7-AF3478E931D3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppName}
; Instalação por usuário (sem UAC). {autopf} vira %LOCALAPPDATA%\Programs quando
; a instalação é só do usuário, e Program Files se o usuário escolher "todos".
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile={#RepoRoot}\assets\gato.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
OutputDir={#RepoRoot}\dist
OutputBaseFilename=pomodoro-gatodoro-x64-setup

[Languages]
#ifdef HasPtBr
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
#endif

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
Source: "{#RepoRoot}\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Ao desinstalar, remove a inicialização com o Windows (valor "Pomodoro" em HKCU\...\Run).
; ValueType none + uninsdeletevalue: não grava nada na instalação, só apaga na desinstalação.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "Pomodoro"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o {#MyAppName}"; Flags: nowait postinstall skipifsilent
