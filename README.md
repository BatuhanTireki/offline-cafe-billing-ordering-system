# ☕ Kafe POS - Offline Adisyon Sistemi

Modern, kullanıcı dostu, internet gerektirmeyen kafe adisyon sistemi.  
**Mevcut sürüm:** `v1.1.0` (kimlik doğrulama, rol bazlı yetki ve opsiyonel Firebase senkronizasyonu)

## 🆕 Son Değişiklikler

- Giriş ekranı eklendi; uygulama artık login ile açılıyor.
- Admin ve garson rolleri için yetkilendirme getirildi.
- Menü, rapor ve satış geçmişi sayfaları admin yetkisine bağlandı.
- Firebase Firestore için opsiyonel senkronizasyon katmanı eklendi.
- Açılışta isteğe bağlı tam senkronizasyon desteği getirildi.
- Varsayılan kullanıcılar: `admin/admin123` ve `garson/garson123`.

## 🎯 Özellikler

### ✅ Masa Yönetimi
- 40 masa kapasitesi
- Masa durumu göstergesi (boş / açık / dolu)
- Renk kodlu görsel arayüz
- Ürün eklendikçe otomatik durum ve toplam güncelleme

### 🍽️ Ürün ve Menü Yönetimi
- Kategori bazlı ürün organizasyonu
- Ürün ekleme, silme, güncelleme (modal ile düzenleme)
- Fiyat yönetimi (backend ve frontend tarafında validasyon)
- Kategori filtreleme ve metinle ürün arama

### 📝 Adisyon Sistemi
- Hızlı ürün ekleme
- Adet artırma/azaltma
- Ürün silme
- Anlık toplam hesaplama (2 ondalık hassasiyet, güvenli fiyat formatlama)
- Yanlış girişleri düzeltme

### 💳 Ödeme
- Nakit ödeme
- Kart ödeme
- Otomatik masa kapatma
- Satış kaydı oluşturma

### 🔐 Kimlik Doğrulama ve Yetki
- Kullanıcı girişi
- Token tabanlı oturum yönetimi
- Admin / garson rol ayrımı
- Sayfa ve API bazlı yetkilendirme

### ☁️ Opsiyonel Firebase Senkronizasyonu
- Masa, ürün, sipariş ve satış verilerini Firestore'a kopyalama
- Event log kaydı
- Başlangıçta tam senkron tetikleme desteği

### 📊 Raporlama
- Günlük satış raporu
- Ürün bazlı satış analizi
- Kategori bazlı satış
- Nakit/Kart toplam ayrımı
- Tarih filtreleme

## 🏗️ Teknik Mimari

```
┌─────────────────┐
│   Electron      │  ← Frontend (Desktop UI)
│   (Renderer)    │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   Flask API     │  ← Backend (REST API)
│   (Python)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   SQLite DB     │  ← Database (Local)
│   (cafe.db)     │
└─────────────────┘
```

### Teknoloji Yığını

**Frontend:**
- Electron 28.0
- HTML5, CSS3, Vanilla JavaScript
- Responsive tasarım

**Backend:**
- Python 3.x
- Flask 3.0
- Flask-CORS
- Firebase Admin SDK (opsiyonel)

**Database:**
- SQLite3 (local, offline)

**Packaging:**
- PyInstaller (backend → .exe)
- electron-builder (frontend → .exe)

## 📊 Veritabanı Yapısı

### tables (Masalar)
```sql
- id: INTEGER PRIMARY KEY
- table_number: INTEGER UNIQUE
- status: TEXT (empty/occupied)
- opened_at: TIMESTAMP
- total_amount: REAL
```

### categories (Kategoriler)
```sql
- id: INTEGER PRIMARY KEY
- name: TEXT UNIQUE
```

### products (Ürünler)
```sql
- id: INTEGER PRIMARY KEY
- name: TEXT
- price: REAL
- category_id: INTEGER (FK)
- is_active: INTEGER
- created_at: TIMESTAMP
```

### active_orders (Aktif Siparişler)
```sql
- id: INTEGER PRIMARY KEY
- table_id: INTEGER (FK)
- product_id: INTEGER (FK)
- quantity: INTEGER
- unit_price: REAL
- total_price: REAL
- added_at: TIMESTAMP
```

### completed_sales (Tamamlanmış Satışlar)
```sql
- id: INTEGER PRIMARY KEY
- table_number: INTEGER
- total_amount: REAL
- payment_method: TEXT (cash/card)
- sale_date: TIMESTAMP
- opened_at: TIMESTAMP
- closed_at: TIMESTAMP
```

### sale_details (Satış Detayları)
```sql
- id: INTEGER PRIMARY KEY
- sale_id: INTEGER (FK)
- product_name: TEXT
- category_name: TEXT
- quantity: INTEGER
- unit_price: REAL
- total_price: REAL
```

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

- **Python 3.8+** (backend için)
- **Node.js 16+** (frontend için)
- **Windows** işletim sistemi

### 1. Backend Kurulumu

```bash
cd backend

# Sanal ortam oluştur (opsiyonel ama önerilir)
python -m venv venv
venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Backend'i EXE'ye Dönüştürme

```bash
cd backend

# PyInstaller ile paketleme
pyinstaller build_backend.spec

# Oluşan exe: backend/dist/cafe_backend.exe
```

### 3. Frontend Kurulumu

```bash
cd frontend

# Node paketlerini yükle
npm install
```

### 4. Frontend'i EXE'ye Dönüştürme

**ÖNEMLİ:** Önce backend exe'sini oluşturun!

```bash
cd frontend

# Windows exe oluştur
npm run build:win

# Oluşan installer: frontend/dist/Kafe POS Setup.exe
```

### 5. Geliştirme Modunda Çalıştırma

Uygulama açıldığında giriş ekranı gelir. Giriş sonrası ana ekrana yönlenir.

**Varsayılan kullanıcılar:**
- `admin / admin123`
- `garson / garson123`

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 📦 Dağıtım

### Tek Tıkla Çalışır .exe Oluşturma

1. **Backend exe'yi oluştur:**
   ```bash
   cd backend
   pyinstaller build_backend.spec
   ```

2. **Backend exe'yi frontend'e kopyala:**
   ```bash
   mkdir frontend\backend\dist
   copy backend\dist\cafe_backend.exe frontend\backend\dist\
   ```

3. **Frontend installer'ı oluştur:**
   ```bash
   cd frontend
   npm run build:win
   ```

4. **Oluşan dosyalar:**
   - `frontend/dist/Kafe POS Setup.exe` → Installer
   - Kullanıcı bu setup'ı çalıştırır
   - Program başlayınca backend otomatik başlar
   - Kapanınca backend otomatik kapanır

## 🎮 Kullanım Kılavuzu

### Ana Ekran
- 40 masa grid görünümü
- Yeşil: Boş masa
- Pembe: Dolu masa
- Masaya tıklayarak aç/detaya git
- Admin olmayan kullanıcılar menü, rapor ve satış geçmişi ekranlarını göremez

### Masa Detay
- Sol: Menü (kategori filtreli)
- Sağ: Adisyon
- Ürün ekle: Menüden tıkla
- Adet artır/azalt: +/- butonları
- Ürün sil: Çöp kutusu ikonu
- Ödeme al: Nakit veya Kart butonu

### Menü Yönetimi
- Yeni ürün ekle
- Mevcut ürünleri düzenle
- Ürün sil
- Fiyat güncelle

### Raporlar
- Tarih seç
- Günlük ciro görüntüle
- Ürün satış detayları
- Kategori analizi
- Nakit/Kart dağılımı

## 🔧 Sorun Giderme

### Backend başlamıyor
- Port 5000 meşgul olabilir
- Otomatik alternatif port bulur (5001, 5002...)
- Console loglarını kontrol edin

### Veritabanı hatası
- `backend/data/cafe.db` dosyasını silin
- Yeniden başlatın (otomatik oluşur)

### Electron penceresi açılmıyor
- Backend'in başladığından emin olun
- 10 saniye bekleyin
- DevTools'u kontrol edin (Ctrl+Shift+I)

### Network hatası
- Firewall backend.exe'yi blokluyor olabilir
- Windows Güvenlik Duvarı'ndan izin verin

## 📝 Geliştirme Notları

### Port Yönetimi
- Backend başlarken boş port otomatik bulur
- Electron bu port'u dinler
- IPC ile iletişim

### SQLite Path
- EXE modunda: executable yanında `data/` klasörü
- Dev modunda: backend dizininde `data/` klasörü
- Otomatik klasör oluşturma

### Modüler Yapı
- `database.py`: Veritabanı yönetimi
- `models.py`: İş mantığı
- `routes/`: API endpoint'leri
- `main.js`: Electron ana process
- `pages/`: HTML sayfaları

## 🎨 Özelleştirme

### Renk Teması Değiştirme
`index.html`, `table.html` vb. dosyalardaki CSS gradient'lerini düzenleyin:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Masa Sayısını Değiştirme
`database.py` → `_initialize_tables_if_needed()` → range değerini değiştirin:

```python
for i in range(1, 41):  # 41 yerine istediğiniz sayı + 1
```

### Varsayılan Ürünler
`database.py` → `_initialize_sample_data_if_needed()` → products listesini düzenleyin

## 📄 Lisans

MIT License - Ticari ve kişisel kullanıma açık

## 🤝 Destek

Sorun bildirmek için GitHub Issues kullanın.

## 🎯 Roadmap

- [ ] Çoklu kullanıcı yönetimi
- [ ] Fiş yazdırma
- [ ] Stok takibi
- [ ] Garson ataması
- [ ] İndirim/kampanya sistemi
- [ ] Bulut yedekleme

---

**Geliştirici:** Kafe POS Team  
**Versiyon:** 1.0.2  
**Tarih:** Şubat 2026
