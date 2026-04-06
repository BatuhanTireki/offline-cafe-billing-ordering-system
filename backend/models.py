"""
İş mantığı ve veritabanı işlemlerini yöneten model sınıfları
"""

from datetime import datetime
from database import db

# Firebase senkronizasyon fonksiyonlarını isteğe bağlı import et
try:
    from firebase_client import (
        push_table,
        push_product,
        push_active_orders,
        push_sale,
        push_category,
        push_event,
    )
except Exception:  # Eğer firebase yoksa no-op fonksiyonlar kullan
    def push_table(*_, **__):
        pass

    def push_product(*_, **__):
        pass

    def push_active_orders(*_, **__):
        pass

    def push_sale(*_, **__):
        pass

    def push_category(*_, **__):
        pass

    def push_event(*_, **__):
        pass

class TableModel:
    """Masa yönetimi"""
    
    @staticmethod
    def get_all_tables():
        """Tüm masaları listele - status: empty, open, occupied"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.table_number, t.status, t.opened_at, t.total_amount,
                   (SELECT COUNT(*) FROM active_orders WHERE table_id = t.id) as order_count
            FROM tables t
            ORDER BY t.table_number
        """)
        rows = cursor.fetchall()
        tables = []
        for row in rows:
            t = dict(row)
            # Ürün yoksa 'occupied' bile olsa 'open' göster (masa boş açılmış)
            if t['status'] == 'occupied' and (t.pop('order_count', 0) or 0) == 0:
                t['status'] = 'open'
            tables.append(t)
        conn.close()
        return tables
    
    @staticmethod
    def get_table(table_id):
        """Tek masa bilgisi"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
        row = cursor.fetchone()
        table = dict(row) if row else None
        conn.close()
        return table
    
    @staticmethod
    def open_table(table_id):
        """Masayı aç - status 'open' (ürün eklenince 'occupied' olur)"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tables 
            SET status = 'open', opened_at = ?, total_amount = 0.0
            WHERE id = ?
        """, (datetime.now().isoformat(), table_id))
        conn.commit()
        conn.close()

        # Firebase'e masa durumunu gönder (hata durumunda POS etkilenmez)
        try:
            table = TableModel.get_table(table_id)
            if table:
                push_table(table)
            push_event("table.opened", {"table_id": table_id})
        except Exception:
            pass
        return True
    
    @staticmethod
    def close_table(table_id, payment_method):
        """
        Masayı kapat ve satışı kaydet
        payment_method: 'cash' veya 'card'
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Masa bilgilerini al
        cursor.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
        table = dict(cursor.fetchone())
        
        if table['status'] not in ('occupied', 'open'):
            conn.close()
            return False
        
        # Aktif siparişleri al
        cursor.execute("""
            SELECT ao.*, p.name as product_name, c.name as category_name
            FROM active_orders ao
            JOIN products p ON ao.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE ao.table_id = ?
        """, (table_id,))
        orders = [dict(row) for row in cursor.fetchall()]
        
        if not orders:
            conn.close()
            return False
        
        # Satış kaydı oluştur
        cursor.execute("""
            INSERT INTO completed_sales 
            (table_number, total_amount, payment_method, opened_at, closed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            table['table_number'],
            table['total_amount'],
            payment_method,
            table['opened_at'],
            datetime.now().isoformat()
        ))
        sale_id = cursor.lastrowid
        
        # Satış detaylarını kaydet
        for order in orders:
            cursor.execute("""
                INSERT INTO sale_details
                (sale_id, product_name, category_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sale_id,
                order['product_name'],
                order['category_name'],
                order['quantity'],
                order['unit_price'],
                order['total_price']
            ))
        
        # Aktif siparişleri sil
        cursor.execute("DELETE FROM active_orders WHERE table_id = ?", (table_id,))
        
        # Masayı sıfırla
        cursor.execute("""
            UPDATE tables 
            SET status = 'empty', opened_at = NULL, total_amount = 0.0
            WHERE id = ?
        """, (table_id,))
        
        conn.commit()
        conn.close()

        # Firebase'e satış ve masa güncellemesi gönder
        try:
            # Satış header'ını ve detaylarını tekrar oku
            conn2 = db.get_connection()
            cur2 = conn2.cursor()
            cur2.execute("SELECT * FROM completed_sales WHERE id = ?", (sale_id,))
            sale_row = cur2.fetchone()
            sale_header = dict(sale_row) if sale_row else {
                "id": sale_id,
                "table_number": table["table_number"],
                "total_amount": table["total_amount"],
                "payment_method": payment_method,
                "opened_at": table["opened_at"],
                "closed_at": datetime.now().isoformat(),
                "sale_date": datetime.now().isoformat(),
            }
            cur2.execute("SELECT * FROM sale_details WHERE sale_id = ?", (sale_id,))
            details = [dict(r) for r in cur2.fetchall()]
            conn2.close()

            push_sale(sale_header, details)

            # Son masa durumunu da gönder
            final_table = TableModel.get_table(table_id)
            if final_table:
                push_table(final_table)
            push_event("table.closed", {
                "table_id": table_id,
                "sale_id": sale_id,
                "payment_method": payment_method,
                "total_amount": table.get("total_amount"),
            })
        except Exception:
            pass
        return True
    
    @staticmethod
    def update_table_total(table_id):
        """Masa toplam tutarını güncelle"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tables
            SET total_amount = (
                SELECT COALESCE(SUM(total_price), 0)
                FROM active_orders
                WHERE table_id = ?
            )
            WHERE id = ?
        """, (table_id, table_id))
        conn.commit()
        conn.close()


class OrderModel:
    """Sipariş yönetimi"""
    
    @staticmethod
    def get_table_orders(table_id):
        """Masanın aktif siparişlerini getir"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ao.*, p.name as product_name
            FROM active_orders ao
            JOIN products p ON ao.product_id = p.id
            WHERE ao.table_id = ?
            ORDER BY ao.added_at DESC
        """, (table_id,))
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return orders
    
    @staticmethod
    def add_product_to_table(table_id, product_id, quantity=1):
        """Masaya ürün ekle veya mevcut ürünün adedini artır"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Ürün fiyatını al
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        price = result['price']
        
        # Aynı üründen daha önce eklenmiş mi kontrol et
        cursor.execute("""
            SELECT id, quantity FROM active_orders
            WHERE table_id = ? AND product_id = ?
        """, (table_id, product_id))
        existing = cursor.fetchone()
        
        if existing:
            # Mevcut ürünün adedini artır
            new_quantity = int(existing['quantity']) + int(quantity)
            new_total = round(new_quantity * float(price), 2)
            cursor.execute("""
                UPDATE active_orders
                SET quantity = ?, total_price = ?
                WHERE id = ?
            """, (new_quantity, new_total, existing['id']))
        else:
            # Yeni ürün ekle
            total_price = round(float(price) * int(quantity), 2)
            cursor.execute("""
                INSERT INTO active_orders
                (table_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (table_id, product_id, quantity, float(price), total_price))
        
        conn.commit()
        # Masaya ürün eklendiğinde status'u occupied yap
        cursor.execute("UPDATE tables SET status = 'occupied' WHERE id = ?", (table_id,))
        conn.commit()
        conn.close()
        
        # Masa toplamını güncelle
        TableModel.update_table_total(table_id)

        # Firebase: aktif siparişler ve masa toplamını gönder
        try:
            orders = OrderModel.get_table_orders(table_id)
            push_active_orders(table_id, orders)
            table = TableModel.get_table(table_id)
            if table:
                push_table(table)
            push_event("order.added", {
                "table_id": table_id,
                "product_id": product_id,
                "quantity": int(quantity),
            })
        except Exception:
            pass
        return True
    
    @staticmethod
    def update_order_quantity(order_id, new_quantity):
        """Sipariş adedini güncelle"""
        if new_quantity < 1:
            return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT unit_price, table_id FROM active_orders WHERE id = ?
        """, (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return False
        
        new_total = round(float(order['unit_price']) * int(new_quantity), 2)
        cursor.execute("""
            UPDATE active_orders
            SET quantity = ?, total_price = ?
            WHERE id = ?
        """, (int(new_quantity), new_total, order_id))
        
        conn.commit()
        table_id = order['table_id']
        conn.close()
        
        # Masa toplamını güncelle
        TableModel.update_table_total(table_id)

        # Firebase senkron
        try:
            orders = OrderModel.get_table_orders(table_id)
            push_active_orders(table_id, orders)
            table = TableModel.get_table(table_id)
            if table:
                push_table(table)
            push_event("order.quantity_updated", {
                "order_id": order_id,
                "table_id": table_id,
                "new_quantity": int(new_quantity),
            })
        except Exception:
            pass
        return True
    
    @staticmethod
    def remove_order(order_id):
        """Siparişi adisyondan sil"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT table_id FROM active_orders WHERE id = ?", (order_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        table_id = result['table_id']
        cursor.execute("DELETE FROM active_orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        
        # Masa toplamını güncelle
        TableModel.update_table_total(table_id)

        # Firebase senkron
        try:
            orders = OrderModel.get_table_orders(table_id)
            push_active_orders(table_id, orders)
            table = TableModel.get_table(table_id)
            if table:
                push_table(table)
            push_event("order.removed", {
                "order_id": order_id,
                "table_id": table_id,
            })
        except Exception:
            pass
        return True


class MenuModel:
    """Menü yönetimi"""
    
    @staticmethod
    def get_all_categories():
        """Tüm kategorileri getir"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categories
    
    @staticmethod
    def get_all_products():
        """Tüm ürünleri kategorileriyle getir"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            ORDER BY c.name, p.name
        """)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products
    
    @staticmethod
    def add_product(name, price, category_id):
        """Yeni ürün ekle"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, price, category_id)
            VALUES (?, ?, ?)
        """, (name, price, category_id))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()

        # Firebase'e ürün güncellemesi gönder
        try:
            product = {
                "id": product_id,
                "name": name,
                "price": price,
                "category_id": category_id,
                "is_active": 1,
            }
            push_product(product)
            push_event("product.added", {"product_id": product_id, "name": name})
        except Exception:
            pass
        return product_id
    
    @staticmethod
    def update_product(product_id, name, price, category_id):
        """Ürün güncelle"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products
            SET name = ?, price = ?, category_id = ?
            WHERE id = ?
        """, (name, price, category_id, product_id))
        conn.commit()
        conn.close()

        # Firebase'e ürün güncellemesi gönder
        try:
            product = {
                "id": product_id,
                "name": name,
                "price": price,
                "category_id": category_id,
                "is_active": 1,
            }
            push_product(product)
            push_event("product.updated", {"product_id": product_id, "name": name})
        except Exception:
            pass
        return True
    
    @staticmethod
    def delete_product(product_id):
        """Ürünü pasif yap (soft delete)"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET is_active = 0 WHERE id = ?
        """, (product_id,))
        conn.commit()
        conn.close()

        # Firebase'e pasif ürün bilgisi gönder
        try:
            product = {
                "id": product_id,
                "is_active": 0,
            }
            push_product(product)
            push_event("product.deleted", {"product_id": product_id})
        except Exception:
            pass
        return True
    
    @staticmethod
    def add_category(name):
        """Yeni kategori ekle"""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            category_id = cursor.lastrowid
            conn.close()
            try:
                push_category({"id": category_id, "name": name})
                push_event("category.added", {"category_id": category_id, "name": name})
            except Exception:
                pass
            return category_id
        except:
            conn.close()
            return None


class ReportModel:
    """Raporlama"""
    
    @staticmethod
    def get_daily_sales(date=None):
        """Günlük satış raporu"""
        if date is None:
            date = datetime.now().date().isoformat()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Toplam satış
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sales,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0) as cash_total,
                COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0) as card_total
            FROM completed_sales
            WHERE DATE(sale_date) = ?
        """, (date,))
        summary = dict(cursor.fetchone())
        
        # Ürün bazlı satış
        cursor.execute("""
            SELECT 
                product_name,
                category_name,
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue
            FROM sale_details sd
            JOIN completed_sales cs ON sd.sale_id = cs.id
            WHERE DATE(cs.sale_date) = ?
            GROUP BY product_name, category_name
            ORDER BY total_revenue DESC
        """, (date,))
        products = [dict(row) for row in cursor.fetchall()]
        
        # Kategori bazlı satış
        cursor.execute("""
            SELECT 
                category_name,
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue
            FROM sale_details sd
            JOIN completed_sales cs ON sd.sale_id = cs.id
            WHERE DATE(cs.sale_date) = ?
            GROUP BY category_name
            ORDER BY total_revenue DESC
        """, (date,))
        categories = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'summary': summary,
            'products': products,
            'categories': categories
        }
    
    @staticmethod
    def get_sales_by_date_range(start_date, end_date):
        """Tarih aralığına göre satış raporu"""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(sale_date) as sale_date,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM completed_sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            GROUP BY DATE(sale_date)
            ORDER BY sale_date DESC
        """, (start_date, end_date))
        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sales
