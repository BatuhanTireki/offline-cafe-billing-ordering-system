# Kafe POS

Offline-first cafe adisyon ve masa yonetim sistemi.

Bu proje, Electron tabanli masaustu arayuz ile Flask REST API backend'ini birlestirir. Ana veri kaynagi SQLite'tir. Ihtiyaca gore Firebase Firestore senkronizasyonu da devreye alinabilir.

## Neler Sunuyor?

- 40 masa icin hizli operasyon akisi (empty/open/occupied)
- Masa bazli adisyon yonetimi
- Urun ekleme, silme, adet guncelleme
- Nakit/Kart odeme ile masa kapatma
- Gunluk satis raporlari ve satis gecmisi
- Rol bazli yetkilendirme (admin/waiter)
- Opsiyonel Firebase senkron katmani

## Teknik Mimari

1. Electron renderer, localhost uzerinden Flask API'ye istek atar.
2. Flask, is kurallarini models katmaninda calistirir.
3. Kalici veriler SQLite'a yazilir.
4. Firebase etkinse degisiklikler Firestore'a da gonderilir.

Teknoloji yiginlari:

- Frontend: Electron, HTML, CSS, JavaScript
- Backend: Python, Flask, Flask-CORS
- Veritabani: SQLite
- Opsiyonel bulut katmani: Firebase Admin SDK
- Paketleme: PyInstaller + electron-builder

## Roller ve Yetkiler

- waiter:
   - masa acma
   - siparis ekleme/guncelleme/silme
   - masa durumlarini goruntuleme
- admin:
   - waiter tum yetkileri
   - menu yonetimi
   - raporlar ve satis gecmisi
   - masa kapatma/odeme
   - Firebase sync endpointleri

Varsayilan kullanicilar:

- admin / admin123
- garson / garson123

## Ekranlar

- login: giris ekrani
- index: masa grid ekrani
- table: masa detay/adisyon ekrani
- menu-management: urun ve kategori yonetimi (admin)
- reports: gunluk raporlama (admin)
- sales-history: tarih aralikli satis gecmisi ve detay (admin)

## API Ozeti

Auth:

- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout

Tables:

- GET /api/tables/
- GET /api/tables/:id
- POST /api/tables/:id/open
- POST /api/tables/:id/close (admin)

Menu:

- GET /api/menu/categories
- POST /api/menu/categories (admin)
- GET /api/menu/products
- POST /api/menu/products (admin)
- PUT /api/menu/products/:id (admin)
- DELETE /api/menu/products/:id (admin)

Orders:

- GET /api/orders/table/:id
- POST /api/orders/add
- PUT /api/orders/:id/quantity
- DELETE /api/orders/:id

Reports:

- GET /api/reports/daily?date=YYYY-MM-DD (admin)
- GET /api/reports/range?start_date=...&end_date=... (admin)

Sales:

- GET /api/sales/history?start_date=...&end_date=... (admin)
- GET /api/sales/:id/details (admin)

Firebase Sync:

- GET /api/sync/firebase/status (admin)
- POST /api/sync/firebase/full (admin)

Saglik endpointleri:

- /
- /health
- /firebase-health

## Kurulum

Gereksinimler:

- Windows 10/11
- Python 3.8+
- Node.js 16+

### Gelistirme Ortami

1. Backend bagimliliklarini kur:

```bash
cd backend
pip install -r requirements.txt
```

2. Frontend bagimliliklarini kur:

```bash
cd ../frontend
npm install
```

3. Uygulamayi baslat:

```bash
npm start
```

Alternatif tek komut:

```bash
run-dev.bat
```

## Build ve Dagitim

Tek adimla build:

```bash
build.bat
```

Beklenen cikti:

- frontend/dist/Kafe POS Setup.exe

Manuel build adimlari icin [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) dosyasina bak.

## Firebase (Opsiyonel)

Firebase etkin degilse uygulama tamamen offline calismaya devam eder.

Desteklenen ortam degiskenleri:

- FIREBASE_ENABLED=true|false
- FIREBASE_CREDENTIALS_PATH=service-account-json-yolu
- FIREBASE_BRANCH_ID=default
- FIREBASE_FULL_SYNC_ON_START=true|false

run-dev.bat, gelistirme ortaminda bu degiskenleri otomatik set eder.

## Veritabani Notlari

Ana tablolar:

- tables
- categories
- products
- active_orders
- completed_sales
- sale_details
- users

Ilk acilista:

- tablo yapilari olusturulur
- 40 masa olusturulur
- ornek menu yuklenir
- varsayilan kullanicilar eklenir

## Sorun Giderme

Backend acilmiyorsa:

- backend loglarini kontrol et
- port cakismasi varsa backend otomatik alternatif port bulur

Login tekrar istiyorsa:

- session yapisi bellek icidir
- backend restart sonrasinda tekrar login gerekir

Firebase baglanmiyorsa:

- FIREBASE_CREDENTIALS_PATH degerini kontrol et
- service account dosyasinin mevcut oldugunu dogrula
- FIREBASE_ENABLED degerini kontrol et

## Dokumantasyon

- [QUICKSTART.md](QUICKSTART.md)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- [SETUP_GUIDE.md](SETUP_GUIDE.md)
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)
- [CHANGELOG.md](CHANGELOG.md)

## Lisans

MIT
