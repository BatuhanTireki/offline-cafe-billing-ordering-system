@echo off
set "ROOT_DIR=%~dp0"
echo ============================================
echo   KAFE POS - GELISTIRME MODU
echo ============================================
echo.

echo Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadi! Lutfen Python yukleyin.
    pause
    exit /b 1
)

echo Node.js kontrol ediliyor...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Node.js bulunamadi! Lutfen Node.js yukleyin.
    pause
    exit /b 1
)

echo.
echo Firebase gelistirme ayarlari yapiliyor...
REM Service account dosyanizi backend\firebase-service-account.json olarak kaydedin
set "FIREBASE_ENABLED=true"
set "FIREBASE_CREDENTIALS_PATH=%ROOT_DIR%backend\firebase-service-account.json"
set "FIREBASE_BRANCH_ID=default"
set "FIREBASE_FULL_SYNC_ON_START=true"
echo FIREBASE_ENABLED=%FIREBASE_ENABLED%
echo FIREBASE_CREDENTIALS_PATH=%FIREBASE_CREDENTIALS_PATH%

echo Backend baslatiiliyor...
start "Backend Server" cmd /k "cd /d ""%ROOT_DIR%backend"" && python app.py"

timeout /t 5 /nobreak > nul

echo.
echo Frontend baslatiiliyor...
cd /d "%ROOT_DIR%frontend"
call npm start

pause
