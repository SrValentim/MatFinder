; ============================================================================
; MatFinder - Instalador (Inno Setup 6)
; ============================================================================
; Gera um setup.exe com: pagina de TERMOS (InfoBefore) + LICENCA GPL (aceite) +
; escolha de pasta + atalhos (Menu Iniciar / Area de Trabalho) + desinstalador.
;
; Pre-requisito: o build precisa existir em ..\dist\MatFinder (rode COMPILAR.bat).
; Compilar (da raiz do projeto):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_tools\MatFinder.iss
; Saida: ..\dist\installer\MatFinder-<versao>-Setup.exe
; ============================================================================

#define AppName "MatFinder"
#define AppVersion "3.26.0"
#define AppPublisher "Raynner Valentim - UFAM"
#define AppURL "https://github.com/SrValentim/MatFinder"
#define AppExe "MatFinder.exe"

[Setup]
AppId={{9C2B7E54-3A1D-4F8B-B6E0-2D4F8A1C7E90}
AppName={#AppName}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputBaseFilename=MatFinder-{#AppVersion}-Setup
OutputDir=..\dist\installer
SetupIconFile=..\matfinder\assets\icons\polvo.ico
UninstallDisplayIcon={app}\{#AppExe}
LicenseFile=..\licenses\LICENSE_FULL.txt
InfoBeforeFile=installer_terms.txt
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\MatFinder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"
; PhaseDRX Suite: executável próprio (PhaseDRX.exe), com ícone do PhaseDRX
Name: "{group}\PhaseDRX Suite"; Filename: "{app}\PhaseDRX.exe"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\matfinder\assets\icons\PhaseDRX.ico"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{autodesktop}\PhaseDRX Suite"; Filename: "{app}\PhaseDRX.exe"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\matfinder\assets\icons\PhaseDRX.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: files; Name: "{app}\matfinder.log"
Type: files; Name: "{app}\settings.json"
Type: files; Name: "{app}\historico_buscas.json"
Type: files; Name: "{app}\favorites.json"
