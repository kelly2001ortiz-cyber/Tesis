; ====== VARIABLES (puedes editar) ======
#define MyAppName "MiApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kelly"
#define MyAppExeName "MiApp.exe"

; ====== SETUP ======
[Setup]
; Crea un GUID único (en Inno: Tools > Generate GUID) y pega aquí:
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist_installer
OutputBaseFilename={#MyAppName}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Si tienes icono del instalador, descomenta:
; SetupIconFile=icon.ico
; Si tu app es 64-bit y quieres instalar en Program Files (no x86):
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ====== ARCHIVOS ======
; *** ONEFILE (un solo MiApp.exe) ***
[Files]
Source: "dist\MiApp.exe"; DestDir: "{app}"; Flags: ignoreversion

; Si usaste modo carpeta (ONEDIR), COMENTA la línea anterior y usa esta:
; Source: "dist\MiApp\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

; ====== ACCESOS DIRECTOS ======
[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Atajos:"; Flags: unchecked

; ====== POST-INSTALACIÓN ======
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent
