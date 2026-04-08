# Kafe POS

Guncel masa yonetimi, adisyon, raporlama ve opsiyonel Firebase senkronizasyonu iceren Electron + Flask tabanli cafe POS uygulamasi.

## Ozet

- Frontend: Electron + HTML/CSS/JS
- Backend: Flask REST API
- Veritabani: SQLite (ana kaynak)
- Opsiyonel senkron: Firebase Firestore
- Kimlik dogrulama: token tabanli session
- Roller: admin, waiter

## Temel Ozellikler

- 40 masa (empty/open/occupied durumlari)
- urun ekleme/silme, adet guncelleme
- menu yonetimi (admin)
- masa kapatma ve odeme (admin)
- gunluk raporlar (admin)
- satis gecmisi ve satis detay modal'i (admin)
- Firebase event ve veri senkronu (opsiyonel)

## Hemen Basla

### Gelistirme

1. backend bagimliliklari:

   cd backend
   pip install -r requirements.txt

2. frontend bagimliliklari:

   cd ../frontend
   npm install

3. uygulamayi ac:

   npm start

Alternatif: proje kokunden run-dev.bat calistir.

### Build

Tek adim: proje kokunden build.bat calistir.

Beklenen cikti:
- frontend/dist/Kafe POS Setup.exe

## Varsayilan Kullanici Bilgileri

- admin / admin123
- garson / garson123

## Firebase (Opsiyonel)

Firebase kapali olsa da uygulama normal calisir.

Kullanilan ortam degiskenleri:
- FIREBASE_ENABLED=true|false
- FIREBASE_CREDENTIALS_PATH=service account json yolu
- FIREBASE_BRANCH_ID=default
- FIREBASE_FULL_SYNC_ON_START=true|false

Not: run-dev.bat bu degiskenleri gelistirme icin otomatik ayarlar.

## API Gruplari

- /api/auth
- /api/tables
- /api/menu
- /api/orders
- /api/reports
- /api/sales
- /api/sync

Ek saglik endpointleri:
- /
- /health
- /firebase-health

## Rol Yetkilendirme

- waiter:
  masa acma, siparis islemleri
- admin:
  waiter yetkileri + menu, rapor, satis gecmisi, masa kapatma, firebase sync

## Proje Yapisi

Detayli guncel yapi icin PROJECT_STRUCTURE.md dosyasina bak.

## Sorun Giderme

Backend acilmiyorsa:
- backend otomatik bos port bulur (5000+)
- backend loglarini kontrol et

Login surekli dusuyorsa:
- session'lar backend belleginde tutulur
- backend yeniden baslayinca yeniden login gerekir

Firebase baglanti hatasi varsa:
- service account yolu ve dosya varligini kontrol et
- FIREBASE_ENABLED degerini kontrol et

## Lisans

MIT
