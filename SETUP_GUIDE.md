# Kafe POS - Setup Guide (Guncel)

Bu dosya, kurulum ve kullanimin kisa ozetidir. Kodla birebir uyumludur.

## Gereksinimler

- Windows 10/11
- Python 3.8+
- Node.js 16+

## Kurulum (Build)

1. Proje kokunde build.bat calistir.
2. Script backend exe ve frontend installer uretir.
3. Cikti dosyasi:
   frontend/dist/Kafe POS Setup.exe

## Gelistirme Modu

1. Proje kokunde run-dev.bat calistir.
2. Script backend'i Python ile baslatir.
3. Script frontend'i npm start ile acar.

Notlar:
- Backend bos portu otomatik bulur (5000+).
- Frontend backend portunu IPC ile alir.

## Giris

Varsayilan hesaplar:
- admin / admin123
- garson / garson123

Rol yetkileri:
- garson: masa ve siparis islemleri
- admin: menu, rapor, satis gecmisi, masa kapatma, Firebase sync

## Firebase (Opsiyonel)

Firebase kapaliysa uygulama normal sekilde offline calisir.

Desteklenen ortam degiskenleri:
- FIREBASE_ENABLED=true|false
- FIREBASE_CREDENTIALS_PATH=service account dosya yolu
- FIREBASE_BRANCH_ID=default
- FIREBASE_FULL_SYNC_ON_START=true|false

API endpointleri:
- GET /api/sync/firebase/status (admin)
- POST /api/sync/firebase/full (admin)
- GET /firebase-health (debug)

## Kullanim Akisi

1. Login ol.
2. Bos masayi ac.
3. Urun ekle/sil, adet guncelle.
4. Admin ile odeme al ve masayi kapat.
5. Admin ekranlarinda rapor/satis gecmisi gor.

## Sik Sorunlar

Backend acilmiyorsa:
- Port ve log kontrolu yap.

Login dusuyorsa:
- Sessionlar bellek icinde tutulur; backend restart sonrasi tekrar login gerekir.

Veritabani sifirlama:
- backend/data/cafe.db dosyasini sil, yeniden baslat.

## Ilgili Dokumanlar

- README.md
- QUICKSTART.md
- PROJECT_STRUCTURE.md
- BUILD_INSTRUCTIONS.md
