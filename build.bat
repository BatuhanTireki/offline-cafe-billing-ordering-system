@echo off
echo ============================================
echo   KAFE POS - EXE BUILDER
echo ============================================
echo.

echo Python surumu kontrol ediliyor...
set "PY_CMD="
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3.11"
) else (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo HATA: Python bulunamadi!
        echo Cozum: Python 3.11 kurun ve tekrar deneyin.
        pause
        exit /b 1
    )
    set "PY_CMD=python"
)

echo Kullanilan yorumlayici: %PY_CMD%
echo.

echo [1/5] Gerekli klasorleri olusturuluyor...
if not exist "backend\dist" mkdir backend\dist
if not exist "frontend\assets" mkdir frontend\assets
if not exist "frontend\backend\dist" mkdir frontend\backend\dist
echo   Klasorler hazir!

echo.
echo [2/5] Backend bagimliliklari kontrol ediliyor...
cd backend
%PY_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo HATA: Backend bagimliliklari yuklenemedi!
    pause
    exit /b 1
)

echo.
echo [3/5] Backend exe olusturuluyor...
%PY_CMD% -m PyInstaller --clean build_backend.spec
if %errorlevel% neq 0 (
    echo HATA: Backend exe olusturulamadi!
    echo Not: Python 3.10.0 ile PyInstaller hatasi alinabilir. Python 3.11 onerilir.
    pause
    exit /b 1
)

echo.
echo [4/5] Backend exe frontend'e kopyalaniyor...
copy dist\cafe_backend.exe ..\frontend\backend\dist\cafe_backend.exe
if %errorlevel% neq 0 (
    echo UYARI: Backend exe kopyalanamadi, manuel kopyalayiniz!
)

if exist firebase-service-account.json (
    copy firebase-service-account.json ..\frontend\backend\firebase-service-account.json >nul
    if %errorlevel% neq 0 (
        echo UYARI: Firebase credentials dosyasi kopyalanamadi.
    )
) else (
    echo BILGI: firebase-service-account.json bulunamadi, Firebase offline modda kalacak.
)

echo.
echo [5/5] Frontend exe olusturuluyor...
cd ..\frontend
call npm install
if %errorlevel% neq 0 (
    echo HATA: Frontend bagimliliklari yuklenemedi!
    pause
    exit /b 1
)

call npm run build:win
if %errorlevel% neq 0 (
    echo HATA: Frontend exe olusturulamadi!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD TAMAMLANDI!
echo ============================================
echo.
echo Installer konumu: frontend\dist\Kafe POS Setup.exe
echo.
pause
