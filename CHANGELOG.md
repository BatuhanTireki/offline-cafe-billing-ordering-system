# 📝 CHANGELOG

Tüm önemli değişiklikler bu dosyada belgelenir.

---

## [1.1.0] - 2026-04-06

### 🔐 Kimlik Doğrulama ve Yetkilendirme

#### Backend
- `auth.py` eklendi: token tabanlı oturum yönetimi
- `routes/auth_routes.py` eklendi: login, me, logout endpoint'leri
- `routes/*` içinde yetki kontrolü eklendi
- Kullanıcılar tablosu ve varsayılan kullanıcılar oluşturuldu

#### Frontend
- Giriş ekranı eklendi
- Admin olmayan kullanıcılar için menü, rapor ve satış geçmişi gizlendi
- API isteklerine Authorization header desteği eklendi

### ☁️ Firebase Senkronizasyonu

#### Backend
- `firebase_client.py` eklendi: Firestore senkron katmanı
- `routes/sync.py` eklendi: Firebase durum ve tam senkron endpoint'leri
- Masa, ürün, sipariş ve satış değişiklikleri için Firestore push desteği eklendi
- Açılışta isteğe bağlı tam senkronizasyon desteği eklendi

#### Dağıtım
- `run-dev.bat` Firebase geliştirme değişkenleri ile güncellendi
- `backend/requirements.txt` içine `firebase-admin` eklendi

### 📝 Dokümantasyon
- `README.md` yeni giriş ve senkronizasyon akışını açıklayacak şekilde güncellendi

## [1.0.2] - 2026-02-22

### 🐛 Fiyat ve Miktar Bugları Düzeltildi

#### Backend
- **menu.py:** Fiyat validasyonu eklendi (negatif/0 reddi, güvenli float parse, round 2 ondalık)
- **menu.py:** Geçersiz fiyat girdisinde anlamlı hata mesajı (örn: `float("abc")` hatası önlendi)
- **orders.py:** Miktar validasyonu eklendi (pozitif tam sayı zorunlu; string/ondalık adet hatası düzeltildi)
- **models.py:** Fiyat hesaplamalarında `round(..., 2)` ile tutarlı ondalık
- **models.py:** Miktar değerleri integer olarak garanti edildi

#### Frontend
- **formatPrice():** Tüm sayfalarda güvenli fiyat gösterimi; `null`/`undefined` hataları önlendi
- **table.html, menu-management.html, sales-history.html, reports.html, index.html:** formatPrice kullanımı
- **menu-management.html:** Fiyat girişi validasyonu (isNaN, negatif kontrol)
- **menu-management.html:** Ürün düzenlemede geçerli fiyat kontrolü

### ✨ Yeni Özellikler

- **Ürün arama:** Menü yönetimi ve masa sayfasında anlık ürün arama
- **API hata mesajları:** Sipariş/ürün ekleme-güncelleme hatalarında backend mesajı kullanıcıya gösteriliyor

---

## [1.0.1] - 2026-02-10

### 🐛 Düzeltmeler

#### Backend
- **CRITICAL:** `database.py` - Eksik `sys` import eklendi
- **CRITICAL:** `database.py` - Duplike `sys` import kaldırıldı  
- **CRITICAL:** `models.py` - `get_table()` metodunda double `fetchone()` bug düzeltildi
- Backend standalone test edilebilir hale getirildi

#### Frontend
- **CRITICAL:** Tüm HTML sayfalarında `backendReady` flag ve retry mekanizması eklendi
- **CRITICAL:** `main.js` - Icon dosyası varlık kontrolü eklendi
- **CRITICAL:** `package.json` - Eksik icon referansı kaldırıldı
- API çağrılarında backend hazır olma kontrolü eklendi

#### Build Sistemi
- **MEDIUM:** `build.bat` - Klasör oluşturma adımları eklendi
- **MEDIUM:** `build.bat` - Backend exe otomatik kopyalama eklendi
- **MEDIUM:** `build.bat` - Her adımda hata kontrolü eklendi
- **LOW:** `run-dev.bat` - Python/Node.js version kontrolleri eklendi
- **LOW:** `run-dev.bat` - Backend bekleme süresi 3→5 saniye artırıldı

### 📚 Dokümantasyon
- `BUILD_INSTRUCTIONS.md` - Detaylı build rehberi eklendi
- `BUG_REPORT.md` - Tüm buglar ve düzeltmeleri dokümante edildi
- `CHANGELOG.md` - Değişiklik geçmişi başlatıldı
- `frontend/assets/README.txt` - Icon ekleme rehberi oluşturuldu

### 🔧 Geliştirmeler
- `test-backend.bat` - Backend standalone test scripti eklendi
- Klasör yapısı standartize edildi
- Hata mesajları iyileştirildi
- Build süreci tamamen otomatikleştirildi

### 🗂️ Yeni Dosyalar
```
+ BUILD_INSTRUCTIONS.md
+ BUG_REPORT.md
+ CHANGELOG.md
+ test-backend.bat
+ frontend/assets/README.txt
+ backend/dist/ (klasör)
+ frontend/backend/dist/ (klasör)
```

---

## [1.0.0] - 2026-02-10

### ✨ İlk Sürüm

#### Özellikler
- 40 masa yönetimi
- Kategori bazlı menü sistemi
- Sipariş ekleme/düzenleme/silme
- Adet kontrolü (+/-)
- Nakit/Kart ödeme
- Günlük satış raporları
- Ürün/kategori bazlı analizler
- Offline çalışma

#### Teknik
- **Backend:** Python + Flask + SQLite
- **Frontend:** Electron + HTML/CSS/JS
- **Packaging:** PyInstaller + electron-builder
- **Platform:** Windows 10/11

#### Veritabanı
6 tablo:
- `tables` - Masa bilgileri
- `categories` - Ürün kategorileri
- `products` - Menü ürünleri
- `active_orders` - Aktif siparişler
- `completed_sales` - Tamamlanmış satışlar
- `sale_details` - Satış detayları

#### UI Sayfaları
- Ana ekran (40 masa grid)
- Masa detay & sipariş
- Menü yönetimi
- Satış raporları

#### Dokümantasyon
- README.md - Genel proje dokümantasyonu
- QUICKSTART.md - Hızlı başlangıç kılavuzu
- PROJECT_STRUCTURE.md - Proje yapısı
- SETUP_GUIDE.md - Kurulum özeti

#### Build Scriptleri
- `build.bat` - Otomatik build
- `run-dev.bat` - Geliştirme modu

---

## Versiyonlama

Format: `MAJOR.MINOR.PATCH`

- **MAJOR:** Uyumsuz API değişiklikleri
- **MINOR:** Geriye uyumlu yeni özellikler
- **PATCH:** Geriye uyumlu bug düzeltmeleri

---

## Gelecek Planları

### [1.1.0] - Planlanan
- [ ] Garson yönetimi
- [ ] Masa rezervasyonu
- [ ] İndirim sistemi
- [ ] Fiş yazdırma

### [1.2.0] - Planlanan
- [ ] Stok takibi
- [ ] Tedarikçi yönetimi
- [ ] Çoklu kullanıcı
- [ ] Yetkilendirme

### [2.0.0] - Gelecek
- [ ] Bulut senkronizasyon
- [ ] Mobil app entegrasyonu
- [ ] Online sipariş
- [ ] QR kod menü
