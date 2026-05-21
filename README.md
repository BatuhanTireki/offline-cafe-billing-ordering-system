# Kafe POS

Cafe adisyon ve masa yonetim sistemi.

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

- admin / admin
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

Cafe receipt and table management system.

This project combines an Electron-based desktop interface with a Flask REST API backend. SQLite is used as the primary data source. Firebase Firestore synchronization can also be enabled when needed.

What Does It Offer?
Fast operational workflow for 40 tables (empty/open/occupied)
Table-based order and receipt management
Add, remove, and update product quantities
Close tables with cash/card payments
Daily sales reports and sales history
Role-based authorization (admin/waiter)
Optional Firebase synchronization layer
Technical Architecture

The Electron renderer sends requests to the Flask API through localhost.
Flask executes business logic in the models layer.
Persistent data is stored in SQLite.
If Firebase is enabled, changes are also synchronized with Firestore.

Technology Stack
Frontend: Electron, HTML, CSS, JavaScript
Backend: Python, Flask, Flask-CORS
Database: SQLite
Optional Cloud Layer: Firebase Admin SDK
Packaging: PyInstaller + electron-builder
Roles and Permissions
waiter
Open tables
Add/update/delete orders
View table statuses
admin
All waiter permissions
Menu management
Reports and sales history
Table closing/payment processing
Firebase sync endpoints
Default Users
admin / admin
garson / garson123
Screens
login: login screen
index: table grid screen
table: table details/order screen
menu-management: product and category management (admin)
reports: daily reporting (admin)
sales-history: sales history and details by date range (admin)
API Summary
Auth
POST /api/auth/login
GET /api/auth/me
POST /api/auth/logout
Tables
GET /api/tables/
GET /api/tables/:id
POST /api/tables/:id/open
POST /api/tables/:id/close (admin)
Menu
GET /api/menu/categories
POST /api/menu/categories (admin)
GET /api/menu/products
POST /api/menu/products (admin)
PUT /api/menu/products/:id (admin)
DELETE /api/menu/products/:id (admin)
Orders
GET /api/orders/table/:id
POST /api/orders/add
PUT /api/orders/:id/quantity
DELETE /api/orders/:id
Reports
GET /api/reports/daily?date=YYYY-MM-DD (admin)
GET /api/reports/range?start_date=...&end_date=... (admin)
Sales
GET /api/sales/history?start_date=...&end_date=... (admin)
GET /api/sales/:id/details (admin)
Firebase Sync
GET /api/sync/firebase/status (admin)
POST /api/sync/firebase/full (admin)
Health Endpoints
/
/health
/firebase-health
Installation
Requirements
Windows 10/11
Python 3.8+
Node.js 16+
Development Environment
Install backend dependencies
cd backend
pip install -r requirements.txt
Install frontend dependencies
cd ../frontend
npm install
Start the application
npm start
Alternative single-command startup
run-dev.bat
Build and Distribution
One-step build
build.bat
Expected output
frontend/dist/Kafe POS Setup.exe

For manual build steps, check the BUILD_INSTRUCTIONS.md file.

Firebase (Optional)

If Firebase is disabled, the application continues to work fully offline.

Supported Environment Variables
FIREBASE_ENABLED=true|false
FIREBASE_CREDENTIALS_PATH=path-to-service-account-json
FIREBASE_BRANCH_ID=default
FIREBASE_FULL_SYNC_ON_START=true|false

run-dev.bat automatically sets these variables in the development environment.

Database Notes
Main Tables
tables
categories
products
active_orders
completed_sales
sale_details
users
On First Launch
Database tables are created
40 tables are generated
Sample menu data is loaded
Default users are added
Troubleshooting
If the backend does not start
Check backend logs
If there is a port conflict, the backend automatically finds an alternative port
If login is repeatedly requested
Session structure is memory-based
You must log in again after a backend restart
If Firebase cannot connect
Check the FIREBASE_CREDENTIALS_PATH value
Verify that the service account file exists
Check the FIREBASE_ENABLED value
Documentation
QUICKSTART.md
PROJECT_STRUCTURE.md
SETUP_GUIDE.md
BUILD_INSTRUCTIONS.md
CHANGELOG.md
License

MIT
