"""
Firebase Firestore senkronizasyon katmanı.

Amaç:
- SQLite ana veri kaynağı olarak kalır
- Önemli değişiklikler (masa durumu, ürünler, satışlar) isteğe bağlı olarak
  Firestore'a kopyalanır

Notlar:
- Eğer FIREBASE_ENABLED=false veya import/başlangıç hatası olursa tüm fonksiyonlar
  sessizce no-op çalışır. Böylece POS tamamen offline da sorunsuz kullanılır.
"""

import os
from datetime import datetime

_firebase_enabled = os.getenv("FIREBASE_ENABLED", "false").lower() == "true"
_firestore = None


def _init_firestore():
    """Lazily initialize Firestore client."""
    global _firestore, _firebase_enabled
    if not _firebase_enabled:
        return None

    if _firestore is not None:
        return _firestore

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
        if not cred_path:
            print("[firebase] FIREBASE_CREDENTIALS_PATH tanımlı değil, senkron kapalı.")
            _firebase_enabled = False
            return None

        if not os.path.isfile(cred_path):
            print(f"[firebase] Service account bulunamadı: {cred_path}")
            _firebase_enabled = False
            return None

        # firebase_admin zaten init edildiyse tekrar init etme
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        _firestore = firestore.client()
        print("[firebase] Firestore istemcisi hazır.")
        return _firestore
    except Exception as exc:  # Geliştirme kolaylığı için geniş yakalama
        print(f"[firebase] Başlatılamadı, senkron devre dışı. Hata: {exc}")
        _firebase_enabled = False
        _firestore = None
        return None


def _get_branch_id() -> str:
    """Şube / ortam kimliği. İleride çoklu şube için kullanılabilir."""
    return os.getenv("FIREBASE_BRANCH_ID", "default")


def _get_db():
    if not _firebase_enabled:
        return None
    return _init_firestore()


def get_sync_status() -> dict:
    """Firebase bağlantı durumunu debug için döndür."""
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
    return {
        "enabled": _firebase_enabled,
        "credentials_path": cred_path,
        "credentials_exists": os.path.isfile(cred_path) if cred_path else False,
        "branch_id": _get_branch_id(),
        "initialized": _firestore is not None,
    }


def push_product(product: dict):
    """Ürünü Firestore 'products' koleksiyonuna yaz."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    pid = str(product.get("id"))
    if not pid:
        return

    data = {
        "name": product.get("name"),
        "price": float(product.get("price", 0)),
        "categoryId": str(product.get("category_id")) if product.get("category_id") is not None else None,
        "categoryName": product.get("category_name"),
        "isActive": bool(product.get("is_active", 1)),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id)\
          .collection("products").document(pid).set(data, merge=True)
    except Exception as exc:
        print(f"[firebase] push_product hata: {exc}")


def push_category(category: dict):
    """Kategoriyi Firestore 'categories' koleksiyonuna yaz."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    cid = str(category.get("id"))
    if not cid:
        return

    data = {
        "name": category.get("name"),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id) \
          .collection("categories").document(cid).set(data, merge=True)
    except Exception as exc:
        print(f"[firebase] push_category hata: {exc}")


def push_event(event_type: str, payload: dict | None = None):
    """Her iş olayını Firestore event log'una yazar."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    payload = payload or {}

    event_data = {
        "eventType": event_type,
        "payload": payload,
        "createdAt": datetime.utcnow(),
    }
    try:
        db.collection("branches").document(branch_id) \
          .collection("events").add(event_data)
    except Exception as exc:
        print(f"[firebase] push_event hata: {exc}")


def push_table(table: dict):
    """Masa durumunu Firestore 'tables' koleksiyonuna yaz."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    tid = str(table.get("id"))
    if not tid:
        return

    data = {
        "tableNumber": table.get("table_number"),
        "status": table.get("status"),
        "openedAt": table.get("opened_at"),
        "totalAmount": float(table.get("total_amount", 0)),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id)\
          .collection("tables").document(tid).set(data, merge=True)
    except Exception as exc:
        print(f"[firebase] push_table hata: {exc}")


def push_active_orders(table_id: int, orders: list[dict]):
    """Bir masanın aktif siparişlerini Firestore alt koleksiyonuna yazar."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    tid = str(table_id)

    try:
        table_ref = db.collection("branches").document(branch_id)\
                      .collection("tables").document(tid)

        # Eski detayları silmek için batch kullan
        batch = db.batch()
        details_ref = table_ref.collection("activeOrders")
        for doc in details_ref.stream():
            batch.delete(doc.reference)
        batch.commit()

        # Yeni siparişleri ekle
        batch = db.batch()
        for order in orders:
            oid = str(order.get("id") or order.get("order_id") or "")
            if not oid:
                continue
            doc_ref = details_ref.document(oid)
            batch.set(doc_ref, {
                "productId": str(order.get("product_id")),
                "productName": order.get("product_name"),
                "quantity": int(order.get("quantity", 0)),
                "unitPrice": float(order.get("unit_price", 0)),
                "totalPrice": float(order.get("total_price", 0)),
                "updatedAt": datetime.utcnow(),
            })
        batch.commit()
    except Exception as exc:
        print(f"[firebase] push_active_orders hata: {exc}")


def push_sale(sale_header: dict, sale_details: list[dict]):
    """Tamamlanmış satışı ve detaylarını Firestore'a yazar."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    sid = str(sale_header.get("id"))
    if not sid:
        return

    try:
        sale_ref = db.collection("branches").document(branch_id)\
                     .collection("sales").document(sid)

        sale_data = {
            "tableNumber": sale_header.get("table_number"),
            "totalAmount": float(sale_header.get("total_amount", 0)),
            "paymentMethod": sale_header.get("payment_method"),
            "saleDate": sale_header.get("sale_date"),
            "openedAt": sale_header.get("opened_at"),
            "closedAt": sale_header.get("closed_at"),
            "updatedAt": datetime.utcnow(),
        }
        sale_ref.set(sale_data, merge=True)

        # Detaylar
        batch = db.batch()
        details_ref = sale_ref.collection("details")
        for i, det in enumerate(sale_details):
            did = det.get("id")
            doc_ref = details_ref.document(str(did or i))
            batch.set(doc_ref, {
                "productName": det.get("product_name"),
                "categoryName": det.get("category_name"),
                "quantity": int(det.get("quantity", 0)),
                "unitPrice": float(det.get("unit_price", 0)),
                "totalPrice": float(det.get("total_price", 0)),
            })
        batch.commit()
    except Exception as exc:
        print(f"[firebase] push_sale hata: {exc}")


def full_sync_from_sqlite(db_conn_factory):
    """
    SQLite içindeki tüm ana tabloları Firestore'a senkronize et.

    Parametre:
    - db_conn_factory: connection döndüren callable (örn: db.get_connection)
    """
    db = _get_db()
    if not db:
        return {"success": False, "error": "Firebase aktif değil veya başlatılamadı"}

    branch_id = _get_branch_id()
    summary = {
        "categories": 0,
        "products": 0,
        "tables": 0,
        "active_orders": 0,
        "sales": 0,
        "sale_details": 0,
    }

    try:
        conn = db_conn_factory()
        cursor = conn.cursor()

        # 1) Categories
        cursor.execute("SELECT * FROM categories")
        categories = [dict(r) for r in cursor.fetchall()]
        for c in categories:
            db.collection("branches").document(branch_id)\
                .collection("categories").document(str(c["id"])).set({
                    "name": c.get("name"),
                    "updatedAt": datetime.utcnow(),
                }, merge=True)
            summary["categories"] += 1

        # 2) Products
        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
        """)
        products = [dict(r) for r in cursor.fetchall()]
        for p in products:
            push_product(p)
            summary["products"] += 1

        # 3) Tables
        cursor.execute("SELECT * FROM tables")
        tables = [dict(r) for r in cursor.fetchall()]
        for t in tables:
            push_table(t)
            summary["tables"] += 1

        # 4) Active orders
        cursor.execute("""
            SELECT ao.*, p.name as product_name
            FROM active_orders ao
            JOIN products p ON ao.product_id = p.id
            ORDER BY ao.table_id, ao.id
        """)
        active_orders = [dict(r) for r in cursor.fetchall()]
        grouped_orders = {}
        for o in active_orders:
            grouped_orders.setdefault(o["table_id"], []).append(o)
            summary["active_orders"] += 1
        # Her masa için activeOrders'ı senkronize et (boşsa da eski kayıtlar silinsin)
        for t in tables:
            table_id = t["id"]
            push_active_orders(table_id, grouped_orders.get(table_id, []))

        # 5) Completed sales
        cursor.execute("SELECT * FROM completed_sales")
        sales = [dict(r) for r in cursor.fetchall()]
        for s in sales:
            cursor.execute("SELECT * FROM sale_details WHERE sale_id = ?", (s["id"],))
            details = [dict(r) for r in cursor.fetchall()]
            push_sale(s, details)
            summary["sales"] += 1
            summary["sale_details"] += len(details)

        conn.close()

        # Senkron metadata
        db.collection("branches").document(branch_id).set({
            "lastFullSyncAt": datetime.utcnow(),
            "lastFullSyncSummary": summary,
        }, merge=True)

        return {"success": True, "summary": summary}
    except Exception as exc:
        return {"success": False, "error": str(exc), "summary": summary}

