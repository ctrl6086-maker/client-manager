; סקריפט Inno Setup - בונה קובץ התקנה (Setup.exe) רגיל לתוכנה,
; עם אייקון בשולחן העבודה, קיצור בתפריט התחלה, והסרת התקנה תקנית
; דרך "הוספה/הסרה של תוכניות" בווינדוס.
;
; דורש התקנה חד-פעמית של Inno Setup (חינמי): https://jrsoftware.org/isdl.php
; לאחר מכן מריצים את build_installer.bat שמריץ את הסקריפט הזה אוטומטית.

#define MyAppName "ניהול לקוחות Gmail"
#define MyAppVersion "1.0"
#define MyAppExeName "ClientManager.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\ClientManager
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=Output
OutputBaseFilename=ClientManager-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "צור קיצור דרך בשולחן העבודה"; GroupDescription: "קיצורי דרך נוספים:"

[Files]
Source: "dist\ClientManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\הסר התקנה"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "הפעל את התוכנה עכשיו"; Flags: nowait postinstall skipifsilent
