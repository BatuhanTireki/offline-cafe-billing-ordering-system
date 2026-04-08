# Proje Yapisi (Guncel)

Bu dosya, kodun mevcut haliyle birebir uyumlu proje yapisi ve API ozetini verir.

## Klasor Agaci

```
cafe-pos/
├── README.md
├── QUICKSTART.md
├── PROJECT_STRUCTURE.md
├── BUILD_INSTRUCTIONS.md
├── SETUP_GUIDE.md
├── build.bat
├── run-dev.bat
├── test-backend.bat
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── firebase_client.py
│   ├── models.py
│   ├── requirements.txt
│   ├── build_backend.spec
│   ├── firebase-service-account.json
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── menu.py
│   │   ├── orders.py
│   │   ├── reports.py
│   │   ├── sales.py
│   │   ├── sync.py
│   │   └── tables.py
│   └── data/
│       └── cafe.db
└── frontend/
    ├── package.json
    ├── assets/
    ├── backend/
    └── src/
        ├── main.js
        ├── preload.js
        └── pages/
            ├── index.html
            ├── login.html
            ├── menu-management.html
            ├── reports.html
            ├── sales-history.html
            └── table.html
```

## Mimari

1. Electron main process, backend Flask surecini baslatir.
2. Frontend sayfalari localhost API'ye HTTP ile baglanir.
3. Is kurallari backend models katmaninda calisir.
4. Ana veri kaynagi SQLite'tir.
5. Firebase etkinse degisiklikler Firestore'a da senkronlanir.

## Backend Modulleri

- app.py: Flask uygulamasi, health endpointleri, route kaydi, bos port bulma
- auth.py: token tabanli kimlik dogrulama ve rol kontrolu
- database.py: tablo olusturma, seed veriler, varsayilan kullanicilar
- models.py: masa, siparis, menu, rapor is kurallari
- firebase_client.py: opsiyonel Firestore push ve full sync islemleri

## Frontend Sayfalari

- login.html: giris ekrani
- index.html: masa grid ekrani
- table.html: masa detay ve adisyon
- menu-management.html: urun/kategori yonetimi (admin)
- reports.html: gunluk raporlar (admin)
- sales-history.html: satis gecmisi ve detay (admin)

## API Endpoint Ozeti

### Auth
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/logout

### Tables
- GET /api/tables/
- GET /api/tables/:id
- POST /api/tables/:id/open
- POST /api/tables/:id/close (admin)

### Menu
- GET /api/menu/categories
- POST /api/menu/categories (admin)
- GET /api/menu/products
- POST /api/menu/products (admin)
- PUT /api/menu/products/:id (admin)
- DELETE /api/menu/products/:id (admin)

### Orders
- GET /api/orders/table/:id
- POST /api/orders/add
- PUT /api/orders/:id/quantity
- DELETE /api/orders/:id

### Reports
- GET /api/reports/daily?date=YYYY-MM-DD (admin)
- GET /api/reports/range?start_date=...&end_date=... (admin)

### Sales
- GET /api/sales/history?start_date=...&end_date=... (admin)
- GET /api/sales/:id/details (admin)

### Firebase Sync
- GET /api/sync/firebase/status (admin)
- POST /api/sync/firebase/full (admin)
- GET /firebase-health (debug)

## Veritabani Tablolari

1. tables
2. categories
3. products
4. active_orders
5. completed_sales
6. sale_details
7. users

## Yetkilendirme Ozeti

- waiter: masa ve siparis islemleri
- admin: tum waiter yetkileri + menu, rapor, satis gecmisi, masa kapatma, sync

## Guvenlik Notlari

- Electron: context isolation acik, nodeIntegration kapali
- Backend: localhost baglantisi, parametreli SQL sorgulari
- CORS: /api/* icin acik (origins: *)

## Build Ozeti

1. backend exe: pyinstaller build_backend.spec
2. frontend installer: npm run build:win
3. electron-builder, backend exe'yi extraResources ile pakete dahil eder
