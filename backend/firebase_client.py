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
import sys
import threading
from pathlib import Path
from datetime import datetime


def _safe_float(value, default=0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def run_firebase_async(fn, *args, **kwargs):
    """Ağır Firebase yazılarını ana isteği bloke etmeden arka planda çalıştır."""
    def _worker():
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            print(f"[firebase] async {getattr(fn, '__name__', 'fn')} hata: {exc}")

    threading.Thread(target=_worker, daemon=True).start()


def _resolve_credentials_path() -> str:
    """
    Firebase service account dosya yolunu bul.

    Oncelik:
    1) FIREBASE_CREDENTIALS_PATH (varsa VE dosya mevcutsa)
    2) Paketli uygulamada exe yanindaki firebase-service-account.json
    3) Gelistirmede backend/firebase-service-account.json
    """
    env_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    elif env_path:
        print(f"[firebase] FIREBASE_CREDENTIALS_PATH hatalı/mevcut değil: {env_path} (yoksayılıyor)")

    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            exe_dir / "firebase-service-account.json",
            exe_dir.parent / "firebase-service-account.json",
        ])
        # PyInstaller _MEIPASS (--onefile modda temp extraction dizini)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "firebase-service-account.json")
        # Electron extraResources konumu
        candidates.extend([
            exe_dir.parent / "resources" / "backend" / "firebase-service-account.json",
            exe_dir / "resources" / "backend" / "firebase-service-account.json",
        ])
    else:
        base_dir = Path(__file__).resolve().parent
        candidates.append(base_dir / "firebase-service-account.json")

    for p in candidates:
        if p.is_file():
            return str(p)

    return ""


def _is_firebase_enabled() -> bool:
    """
    Firebase etkinlik karari:
    - FIREBASE_DISABLED=true ise kapali
    - Service account dosyasi varsa ac (exe dahil)
    - Aksi halde FIREBASE_ENABLED=true ise ac
    """
    if os.getenv("FIREBASE_DISABLED", "").lower() == "true":
        return False
    if _resolve_credentials_path():
        return True
    return os.getenv("FIREBASE_ENABLED", "").lower() == "true"


_firebase_enabled = _is_firebase_enabled()
_firestore = None

# firebase_admin modülünün kurulu olup olmadığını kontrol et
_firebase_sdk_available = False
try:
    import firebase_admin
    from firebase_admin import credentials as _fb_credentials, firestore as _fb_firestore
    _firebase_sdk_available = True
except ImportError as _imp_err:
    print(f"[firebase] firebase-admin SDK bulunamadi, senkron devre disi. ({_imp_err})")
    _firebase_enabled = False
except Exception as _imp_err:
    print(f"[firebase] firebase-admin SDK yuklenemedi, senkron devre disi. ({_imp_err})")
    _firebase_enabled = False


def _init_firestore():
    """Lazily initialize Firestore client."""
    global _firestore, _firebase_enabled
    if not _firebase_enabled or not _firebase_sdk_available:
        return None

    if _firestore is not None:
        return _firestore

    try:
        cred_path = _resolve_credentials_path()
        if not cred_path:
            print("[firebase] Service account yolu bulunamadi, senkron kapali.")
            _firebase_enabled = False
            return None

        if not os.path.isfile(cred_path):
            print(f"[firebase] Service account bulunamadı: {cred_path}")
            _firebase_enabled = False
            return None

        # firebase_admin zaten init edildiyse tekrar init etme
        if not firebase_admin._apps:
            cred = _fb_credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        _firestore = _fb_firestore.client()
        print(f"[firebase] Firestore hazır. branch={_get_branch_id()} cred={cred_path}")
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
    global _firebase_enabled
    if not _firebase_sdk_available:
        return None
    if not _firebase_enabled and _is_firebase_enabled():
        _firebase_enabled = True
    if not _firebase_enabled:
        return None
    return _init_firestore()


def get_sync_status() -> dict:
    """Firebase bağlantı durumunu debug için döndür."""
    cred_path = _resolve_credentials_path()
    return {
        "enabled": _firebase_enabled,
        "enabled_by_env": os.getenv("FIREBASE_ENABLED"),
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
        "name": product.get("name") or "",
        "price": _safe_float(product.get("price")),
        "categoryId": str(product.get("category_id")) if product.get("category_id") is not None else None,
        "categoryName": product.get("category_name"),
        "isActive": bool(product.get("is_active", 1)),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id)\
          .collection("products").document(pid).set(data, merge=True)
        print(f"[firebase] push_product OK id={pid}")
    except Exception as exc:
        print(f"[firebase] push_product hata (id={pid}): {exc}")


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
        "status": table.get("status") or "empty",
        "openedAt": table.get("opened_at"),
        "totalAmount": _safe_float(table.get("total_amount")),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id)\
          .collection("tables").document(tid).set(data, merge=True)
        print(f"[firebase] push_table OK id={tid} status={data['status']}")
    except Exception as exc:
        print(f"[firebase] push_table hata (id={tid}): {exc}")


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
        details_ref = table_ref.collection("activeOrders")

        new_ids = set()
        batch = db.batch()
        op_count = 0

        for order in orders:
            oid = str(order.get("id") or order.get("order_id") or "")
            if not oid:
                continue
            new_ids.add(oid)
            doc_ref = details_ref.document(oid)
            batch.set(doc_ref, {
                "productId": str(order.get("product_id")),
                "productName": order.get("product_name"),
                "quantity": _safe_int(order.get("quantity")),
                "unitPrice": _safe_float(order.get("unit_price")),
                "totalPrice": _safe_float(order.get("total_price")),
                "updatedAt": datetime.utcnow(),
            }, merge=True)
            op_count += 1
            if op_count >= 450:
                batch.commit()
                batch = db.batch()
                op_count = 0

        for doc in details_ref.stream():
            if doc.id not in new_ids:
                batch.delete(doc.reference)
                op_count += 1
                if op_count >= 450:
                    batch.commit()
                    batch = db.batch()
                    op_count = 0

        if op_count > 0:
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
            "totalAmount": _safe_float(sale_header.get("total_amount")),
            "paymentMethod": sale_header.get("payment_method"),
            "saleDate": sale_header.get("sale_date") or sale_header.get("closed_at"),
            "openedAt": sale_header.get("opened_at"),
            "closedAt": sale_header.get("closed_at"),
            "updatedAt": datetime.utcnow(),
        }
        sale_ref.set(sale_data, merge=True)

        if sale_details:
            batch = db.batch()
            details_ref = sale_ref.collection("details")
            for i, det in enumerate(sale_details):
                did = det.get("id")
                doc_ref = details_ref.document(str(did or i))
                batch.set(doc_ref, {
                    "productName": det.get("product_name"),
                    "categoryName": det.get("category_name"),
                    "quantity": _safe_int(det.get("quantity")),
                    "unitPrice": _safe_float(det.get("unit_price")),
                    "totalPrice": _safe_float(det.get("total_price")),
                })
            batch.commit()
        print(f"[firebase] push_sale OK id={sid} details={len(sale_details)}")
    except Exception as exc:
        print(f"[firebase] push_sale hata (id={sid}): {exc}")


def sync_core_to_firestore(db_conn_factory) -> dict:
    """
    Ürünler, masalar, kategoriler ve satışları Firestore'a yazar.
    Başlangıçta veya manuel tetikleme için (activeOrders hariç).
    """
    db = _get_db()
    if not db:
        return {"success": False, "error": "Firebase aktif değil"}

    branch_id = _get_branch_id()
    summary = {"categories": 0, "products": 0, "tables": 0, "sales": 0}

    try:
        conn = db_conn_factory()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM categories")
        for c in [dict(r) for r in cursor.fetchall()]:
            push_category(c)
            summary["categories"] += 1

        cursor.execute("""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
        """)
        for p in [dict(r) for r in cursor.fetchall()]:
            push_product(p)
            summary["products"] += 1

        cursor.execute("SELECT * FROM tables")
        for t in [dict(r) for r in cursor.fetchall()]:
            push_table(t)
            summary["tables"] += 1

        cursor.execute("SELECT * FROM completed_sales")
        sales = [dict(r) for r in cursor.fetchall()]
        for s in sales:
            cursor.execute("SELECT * FROM sale_details WHERE sale_id = ?", (s["id"],))
            details = [dict(r) for r in cursor.fetchall()]
            push_sale(s, details)
            summary["sales"] += 1

        conn.close()

        db.collection("branches").document(branch_id).set({
            "lastCoreSyncAt": datetime.utcnow(),
            "lastCoreSyncSummary": summary,
        }, merge=True)

        print(f"[firebase] sync_core_to_firestore tamam: {summary}")
        return {"success": True, "summary": summary}
    except Exception as exc:
        print(f"[firebase] sync_core_to_firestore hata: {exc}")
        return {"success": False, "error": str(exc), "summary": summary}


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
        "users": 0,
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

        # 6) Users
        cursor.execute("SELECT id, username, password_hash, role, is_active FROM users")
        users = [dict(r) for r in cursor.fetchall()]
        for u in users:
            push_user(u)
        summary["users"] = len(users)

        conn.close()

        # Senkron metadata
        db.collection("branches").document(branch_id).set({
            "lastFullSyncAt": datetime.utcnow(),
            "lastFullSyncSummary": summary,
        }, merge=True)

        return {"success": True, "summary": summary}
    except Exception as exc:
        return {"success": False, "error": str(exc), "summary": summary}


def push_user(user: dict):
    """Kullanıcıyı Firestore 'users' koleksiyonuna yaz (şifre hash'i dahil)."""
    db = _get_db()
    if not db:
        return

    branch_id = _get_branch_id()
    uid = str(user.get("id"))
    if not uid:
        return

    data = {
        "username": user.get("username"),
        "role": user.get("role"),
        "isActive": bool(user.get("is_active", 1)),
        "updatedAt": datetime.utcnow(),
    }

    try:
        db.collection("branches").document(branch_id) \
          .collection("users").document(uid).set(data, merge=True)
        print(f"[firebase] Kullanıcı senkronize edildi: {user.get('username')}")
    except Exception as exc:
        print(f"[firebase] push_user hata: {exc}")


def pull_users() -> list[dict]:
    """
    Firestore'daki kullanıcıları çek.
    Dönen liste: [{"id": str, "username": ..., "password_hash": ..., "role": ..., "is_active": ...}, ...]
    Firebase bağlı değilse boş liste döner.
    """
    db = _get_db()
    if not db:
        return []

    branch_id = _get_branch_id()
    users = []

    try:
        docs = db.collection("branches").document(branch_id) \
                 .collection("users").stream()
        for doc in docs:
            d = doc.to_dict()
            users.append({
                "id": doc.id,
                "username": d.get("username"),
                "password_hash": d.get("passwordHash"),
                "role": d.get("role", "waiter"),
                "is_active": 1 if d.get("isActive", True) else 0,
            })
        print(f"[firebase] {len(users)} kullanıcı Firestore'dan çekildi.")
    except Exception as exc:
        print(f"[firebase] pull_users hata: {exc}")

    return users


def push_all_users(users_list: list[dict]):
    """Tüm kullanıcıları toplu olarak Firestore'a yaz."""
    for u in users_list:
        push_user(u)

