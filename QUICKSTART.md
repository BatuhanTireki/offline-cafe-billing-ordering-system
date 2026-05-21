# Hizli Baslangic (Guncel)

Bu rehber, mevcut kod yapisina gore hizli kurulum ve calistirma adimlarini anlatir.

## Gereksinimler

1. Python 3.8+
2. Node.js 16+
3. Windows 10/11

## 1) Tek Komutla Build

build.bat dosyasini calistir.

Script otomatik olarak:
- backend bagimliliklarini kurar
- backend exe olusturur
- frontend bagimliliklarini kurar
- Windows installer olusturur

Beklenen cikti:
- frontend/dist/Kafe POS Setup.exe

## 2) Uygulamayi Ac

1. frontend/dist/Kafe POS Setup.exe calistir
2. kurulumu tamamla
3. uygulamayi ac

Ilk acilista login ekrani gelir.

Varsayilan kullanicilar:
- admin / admin
- garson / garson123

## 3) Gelistirme Modu

run-dev.bat dosyasini calistir.

Bu script:
- Firebase gelistirme ortam degiskenlerini set eder
- backend'i Python ile baslatir
- frontend'i npm start ile acar

Not: Firebase dosyasi yoksa backend calismaya devam eder, sync no-op olur.

## Opsiyonel Firebase Ayari

Backend firebase_client.py su degiskenleri kullanir:
- FIREBASE_ENABLED=true|false
- FIREBASE_CREDENTIALS_PATH=service account json yolu
- FIREBASE_BRANCH_ID=default
- FIREBASE_FULL_SYNC_ON_START=true|false

run-dev.bat bu degiskenleri otomatik set eder.

## Rol ve Yetki Ozeti

- garson: masa/siparis islemleri
- admin: menu yonetimi, raporlar, satis gecmisi, masa kapatma, firebase sync

## Satis ve Rapor Ekranlari

- Satis Gecmisi: tarih araligina gore listeler, detay modal acilir
- Raporlar: gunluk ozet, urun bazli ve kategori bazli dagilim

## Sorun Giderme

Python bulunamadi:
- python --version ile kontrol et
- Python PATH'e ekli olmasi gerekir

npm bulunamadi:
- node --version ve npm --version ile kontrol et
- Node.js yeniden kur

Build basarisiz:
1. backend/dist ve frontend/dist klasorlerini temizle
2. build.bat'i tekrar calistir

Backend baglanti hatasi:
- backend otomatik bos port bulur (5000+)
- backend loglarini kontrol et

## Hizli Kullanim Akisi

1. Login ol
2. Bos masa ac
3. Urun ekle/sil, adet guncelle
4. Admin ile odeme al ve masa kapat
5. Rapor/Satis gecmisi ekranlarini kullan
