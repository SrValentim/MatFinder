; Script para Inno Setup do MatFinder
; Salve como MatFinder_setup.iss na pasta raiz do seu projeto MatFinder
; (a mesma pasta que contém OQMD_pyside.py e onde as pastas 'dist' e 'logos' estão)

[Setup]
; --- Informações da Aplicação ---
AppName=MatFinder
AppVersion=3.24
AppPublisher=Raynner Valentim - LabMat
; AppPublisherURL=http://www.seuwebsite.com ; (Opcional: seu website)
; AppSupportURL=http://www.seuwebsite.com/support ; (Opcional: link para suporte)
; AppUpdatesURL=http://www.seuwebsite.com/updates ; (Opcional: link para atualizações)

; --- Diretórios e Nomes de Arquivo ---
; {autopf} resolve para "C:\Program Files" ou "C:\Program Files (x86)"
DefaultDirName={autopf}\MatFinder
; Nome do grupo no Menu Iniciar
DefaultGroupName=MatFinder
; Nome base do arquivo de setup de saída (ex: MatFinder-3.23-setup.exe)
OutputBaseFilename=MatFinder3.23-Setup
; Diretório de saída para o setup.exe (relativo ao local do .iss)
; Cria uma pasta "InstallerOutput" para organizar. (Corrigido de Installer para InstallerOutput)
OutputDir=.\InstallerOutput

; --- Ícones ---
; Ícone para o próprio arquivo de setup.exe
SetupIconFile=.\logos\polvo.ico
; Ícone que aparecerá em "Adicionar ou Remover Programas"
; {app} é o diretório de instalação da aplicação.
UninstallDisplayIcon={app}\MatFinder.exe

; --- Configurações de Instalação ---
; Compressão:
; lzma/lzma2: Melhor compressão, setup menor, instalação mais lenta.
; bzip:       Boa compressão, setup médio, instalação média.
; zip:        Compressão razoável, setup maior, instalação mais rápida.
; none:       Sem compressão, setup enorme, instalação muito rápida.
; Experimente 'bzip' ou 'zip' se 'lzma' estiver muito lento.
Compression=bzip
SolidCompression=yes
; Estilo do assistente de instalação
WizardStyle=modern
; Requer privilégios de administrador para instalar em Arquivos de Programas
PrivilegesRequired=admin
; Linguagem padrão (se múltiplas forem definidas em [Languages])
LanguageDetectionMethod=uilanguage

[Languages]
; Define os idiomas disponíveis para o instalador.
; Os arquivos .isl vêm com a instalação do Inno Setup.
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
; Tarefas opcionais que o usuário pode selecionar
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1; MinVersion: 0,4.1


[Files]
; Esta seção define quais arquivos e pastas serão incluídos no instalador.
; Source: O caminho para os arquivos no seu computador de desenvolvimento (relativo ao local do .iss)
;         O PyInstaller gera a aplicação na pasta "dist\NOME_DA_APP\"
; DestDir: "{app}" é o diretório de instalação escolhido pelo usuário.
; Flags:
;   ignoreversion    - não se preocupa com versões de arquivos ao sobrescrever.
;   recursesubdirs   - inclui todas as subpastas.
;   createallsubdirs - cria todas as subpastas de destino necessárias.

Source: ".\dist\MatFinder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Exemplo de inclusão de um arquivo de licença (opcional):
; Source: ".\doc\License.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Cria atalhos no Menu Iniciar e, opcionalmente, na Área de Trabalho

; Atalho principal no Menu Iniciar
Name: "{group}\MatFinder"; Filename: "{app}\MatFinder.exe"; IconFilename: "{app}\logos\polvo.ico"; WorkingDir: "{app}"

; Atalho para o desinstalador no Menu Iniciar
Name: "{group}\{cm:UninstallProgram,MatFinder}"; Filename: "{uninstallexe}"

; Atalho na Área de Trabalho (se a tarefa "desktopicon" for selecionada)
Name: "{commondesktop}\MatFinder"; Filename: "{app}\MatFinder.exe"; Tasks: desktopicon; IconFilename: "{app}\logos\polvo.ico"; WorkingDir: "{app}"

; Atalho na Barra de Lançamento Rápido (para versões mais antigas do Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\MatFinder"; Filename: "{app}\MatFinder.exe"; Tasks: quicklaunchicon; IconFilename: "{app}\logos\polvo.ico"; WorkingDir: "{app}"


[Run]
; Executa o programa após a instalação, se o usuário desejar.
Filename: "{app}\MatFinder.exe"; Description: "{cm:LaunchProgram,MatFinder}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
; Remove arquivos/pastas adicionais criados pela aplicação durante a desinstalação (opcional)
; Exemplo: remover o arquivo de log e o arquivo de histórico
Type: files; Name: "{app}\matfinder.log"
Type: files; Name: "{app}\historico_buscas.json"
; Se a aplicação criar outras pastas dentro de {app}, liste-as aqui para remoção
; Type: dirifempty; Name: "{app}\alguma_pasta_de_dados_criada_pelo_app"

