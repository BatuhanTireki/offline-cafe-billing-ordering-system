# Build Instructions (Guncel)

Bu dosya, mevcut proje yapisina gore build adimlarini anlatir.

## Gereksinimler

- Windows 10/11
- Python 3.8+
- Node.js 16+

Kontrol:

```bash
python --version
node --version
npm --version
```

## Yontem 1: Otomatik Build (Onerilen)

Proje kokunde build.bat calistir.

Script su adimlari yapar:
1. backend bagimliliklarini kurar
2. pyinstaller ile backend exe uretir
3. exe dosyasini frontend/backend/dist altina kopyalar
4. frontend bagimliliklarini kurar
5. electron-builder ile installer uretir

Beklenen cikti:
- frontend/dist/Kafe POS Setup.exe

## Yontem 2: Manuel Build

### 1) Backend exe

```bash
cd backend
pip install -r requirements.txt
pyinstaller build_backend.spec
```

Kontrol:

```bash
dir dist\cafe_backend.exe
```

### 2) Exe kopyalama

```bash
cd ..
mkdir frontend\backend\dist
copy backend\dist\cafe_backend.exe frontend\backend\dist\cafe_backend.exe
```

### 3) Frontend installer

```bash
cd frontend
npm install
npm run build:win
```

Kontrol:

```bash
dir dist\Kafe POS Setup.exe
```

## Build Sonrasi Dogrulama

1. frontend/dist/Kafe POS Setup.exe calisir.
2. Uygulama acilisinda login ekrani gelir.
3. Login sonrasi masa listesi yuklenir.
4. Backend sureci otomatik acilir/kapanir.

## Firebase Notu

Build icin Firebase zorunlu degildir.
Firebase yoksa uygulama offline calisir.

## Sik Hatalar

Python bulunamiyor:
- Python PATH kontrolu yap.

npm bulunamiyor:
- Node.js kurulumunu/PATH'i kontrol et.

PyInstaller bulunamiyor:

```bash
pip install pyinstaller
```

Frontend build hatasi:

```bash
cd frontend
rmdir /s /q node_modules
npm cache clean --force
npm install
npm run build:win
```

## Dagitim

Son kullaniciya verilecek dosya:
- frontend/dist/Kafe POS Setup.exe
