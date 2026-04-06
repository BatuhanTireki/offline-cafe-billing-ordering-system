"""
Veritabanı yönetimi ve tablo yapılarını tanımlayan modül
SQLite kullanarak offline çalışan bir veritabanı oluşturur
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash

class Database:
    def __init__(self):
        # Veritabanı dosyasını uygulamanın yanında sakla
        self.db_path = self._get_db_path()
        self.init_database()
    
    def _get_db_path(self):
        """Veritabanı yolunu belirle - exe durumunda doğru konumda açılsın"""
        if getattr(sys, 'frozen', False):
            # PyInstaller ile paketlenmiş exe durumu
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal Python çalıştırma
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        db_dir = os.path.join(base_path, 'data')
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'cafe.db')
    
    def get_connection(self):
        """Veritabanı bağlantısı oluştur"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Dict-like erişim için
        return conn
    
    def init_database(self):
        """Tüm tabloları oluştur ve örnek verileri ekle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. MASALAR TABLOSU
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY,
                table_number INTEGER UNIQUE NOT NULL,
                status TEXT DEFAULT 'empty',  -- empty / occupied
                opened_at TIMESTAMP,
                total_amount REAL DEFAULT 0.0
            )
        """)
        
        # 2. KATEGORİLER TABLOSU
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # 3. ÜRÜNLER TABLOSU
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        # 4. AKTİF SİPARİŞLER (Masa üzerindeki ürünler)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES tables(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # 5. TAMAMLANMIŞ SATIŞLAR
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completed_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL,  -- cash / card
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        """)
        
        # 6. SATIŞ DETAYLARI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sale_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                category_name TEXT,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES completed_sales(id)
            )
        """)

        # 7. KULLANICILAR
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,   -- admin / waiter
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
        # İlk kurulumda masaları ve örnek verileri oluştur
        self._initialize_tables_if_needed(cursor, conn)
        self._initialize_sample_data_if_needed(cursor, conn)
        self._initialize_users_if_needed(cursor, conn)
        
        conn.close()
    
    def _initialize_tables_if_needed(self, cursor, conn):
        """40 masayı oluştur (eğer yoksa)"""
        cursor.execute("SELECT COUNT(*) as count FROM tables")
        if cursor.fetchone()['count'] == 0:
            for i in range(1, 41):
                cursor.execute("""
                    INSERT INTO tables (table_number, status, total_amount)
                    VALUES (?, 'empty', 0.0)
                """, (i,))
            conn.commit()
            print("✓ 40 masa oluşturuldu")
    
    def _initialize_sample_data_if_needed(self, cursor, conn):
        """Örnek kategoriler ve ürünler ekle"""
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        if cursor.fetchone()['count'] == 0:
            # Kategoriler
            categories = [
                "Sıcak İçecekler",
                "Soğuk İçecekler",
                "Yiyecekler",
                "Tatlılar"
            ]
            for cat in categories:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
            
            # Ürünler
            products = [
                ("Çay", 15.0, "Sıcak İçecekler"),
                ("Türk Kahvesi", 35.0, "Sıcak İçecekler"),
                ("Nescafe", 30.0, "Sıcak İçecekler"),
                ("Sıcak Çikolata", 40.0, "Sıcak İçecekler"),
                ("Kola", 25.0, "Soğuk İçecekler"),
                ("Fanta", 25.0, "Soğuk İçecekler"),
                ("Ayran", 20.0, "Soğuk İçecekler"),
                ("Su", 10.0, "Soğuk İçecekler"),
                ("Kızarmış Sandviç", 50.0, "Yiyecekler"),
                ("Tost", 45.0, "Yiyecekler"),
                ("Börek", 40.0, "Yiyecekler"),
                ("Kruvasan", 35.0, "Yiyecekler"),
                ("Cheesecake", 60.0, "Tatlılar"),
                ("Brownie", 55.0, "Tatlılar"),
                ("Magnolia", 50.0, "Tatlılar")
            ]
            
            for product_name, price, category_name in products:
                cursor.execute("""
                    INSERT INTO products (name, price, category_id)
                    SELECT ?, ?, id FROM categories WHERE name = ?
                """, (product_name, price, category_name))
            
            conn.commit()
            print("✓ Örnek menü oluşturuldu")

    def _initialize_users_if_needed(self, cursor, conn):
        """Varsayılan kullanıcıları oluştur"""
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()['count'] == 0:
            users = [
                ("admin", "admin123", "admin"),
                ("garson", "garson123", "waiter"),
            ]
            for username, raw_password, role in users:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, is_active)
                    VALUES (?, ?, ?, 1)
                """, (username, generate_password_hash(raw_password), role))
            conn.commit()
            print("✓ Varsayılan kullanıcılar oluşturuldu (admin/garson)")

# Global database instance
db = Database()
