; -- AutoThemeInstaller.iss --
; Script d'installation pour Auto Theme Switch

[Setup]
AppName=Auto Theme Switch
AppVersion=1.7.4
AppPublisher=EnokSeth
DefaultDirName={autopf}\Auto Theme Switch
DefaultGroupName=Auto Theme Switch
OutputDir=userdocs:Inno Setup Builds
OutputBaseFilename=AutoThemeInstaller
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\autotheme.exe

[Files]
Source: "dist\autotheme.exe"; DestDir: "{app}"; DestName: "autotheme.exe"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; Facultatif : Readme ou autres fichiers
; Source: "Readme.txt"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{group}\Auto Theme Switch"; Filename: "{app}\autotheme.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Auto Theme Switch"; Filename: "{app}\autotheme.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le bureau"; GroupDescription: "Icônes supplémentaires:"

[Run]
Filename: "{app}\autotheme.exe"; Description: "Lancer Auto Theme Switch"; Flags: nowait postinstall skipifsilent
