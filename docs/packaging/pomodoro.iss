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

[Code]
// Fecha o Pomodoro aberto antes de copiar os arquivos, sem o usuário precisar
// fazer nada. Os nomes batem com src/pomodoro/instance.py.
//  1. Se o app está aberto (mutex), sinaliza o evento de fechar: o app sai como
//     no "Sair" da bandeja, gravando o bloco em andamento.
//  2. Espera até 5 s o mutex sumir.
//  3. Encerra à força o que sobrar (ex.: versões até 0.0.10, sem o evento).
const
  RunningMutexName = 'PomodoroGatodoroRunning';
  QuitEventName = 'PomodoroGatodoroQuit';
  EVENT_MODIFY_STATE = $0002;
  WaitSteps = 50;  // 50 x 100 ms

function OpenEvent(dwDesiredAccess: Cardinal; bInheritHandle: Boolean; lpName: String): THandle;
  external 'OpenEventW@kernel32.dll stdcall';
function SetEvent(hEvent: THandle): Boolean;
  external 'SetEvent@kernel32.dll stdcall';
function CloseHandle(hObject: THandle): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';

procedure AskRunningAppToQuit;
var
  H: THandle;
  I: Integer;
begin
  if not CheckForMutexes(RunningMutexName) then
    Exit;
  H := OpenEvent(EVENT_MODIFY_STATE, False, QuitEventName);
  if H <> 0 then
  begin
    SetEvent(H);
    CloseHandle(H);
  end;
  I := 0;
  while CheckForMutexes(RunningMutexName) and (I < WaitSteps) do
  begin
    Sleep(100);
    I := I + 1;
  end;
end;

procedure KillRemainingInstances;
var
  ResultCode: Integer;
begin
  // Código 128 = nenhum processo encontrado: tudo certo.
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#MyAppExeName}', '',
    SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  AskRunningAppToQuit;
  KillRemainingInstances;
end;
