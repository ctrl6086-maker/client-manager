@echo off
chcp 65001 >nul
echo ============================================
echo   בונה קובץ התקנה (Setup.exe) לתוכנה...
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo לא נמצא Python על המחשב הזה.
    echo יש להתקין Python מ-https://www.python.org/downloads/
    echo וחשוב לסמן בהתקנה את התיבה "Add python.exe to PATH"
    pause
    exit /b 1
)

echo [1/3] מתקין תלויות נדרשות...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ההתקנה נכשלה. בדוק חיבור אינטרנט ונסה שוב.
    pause
    exit /b 1
)

echo.
echo [2/3] בונה את תוכנת ה-GUI (זה עשוי לקחת דקה-שתיים)...
python -m PyInstaller --onefile --windowed --name ClientManager gui.py
if errorlevel 1 (
    echo הבנייה נכשלה - ראה הודעת שגיאה למעלה.
    pause
    exit /b 1
)

set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo.
    echo ============================================
    echo   חסר עוד רכיב אחד, חד-פעמי: Inno Setup
    echo   זה כלי חינמי שבונה את קובץ ההתקנה עצמו.
    echo   הורד והתקן מכאן ^(Next, Next, Install^):
    echo   https://jrsoftware.org/isdl.php
    echo   לאחר ההתקנה, פשוט הרץ את build_installer.bat שוב.
    echo ============================================
    pause
    exit /b 1
)

echo.
echo [3/3] בונה את קובץ ההתקנה עצמו...
%ISCC% installer.iss
if errorlevel 1 (
    echo בניית ההתקנה נכשלה - ראה הודעת שגיאה למעלה.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   הצלחה! קובץ ההתקנה מוכן:
echo   Output\ClientManager-Setup.exe
echo.
echo   זה הקובץ שמריצים כדי "להתקין" את התוכנה -
echo   בדיוק כמו כל תוכנה אחרת שמורידים מהאינטרנט.
echo   אפשר להעביר אותו למחשבים אחרים בעסק גם כן.
echo ============================================
pause
