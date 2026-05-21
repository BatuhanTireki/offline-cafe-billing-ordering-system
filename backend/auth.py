"""
Basit token tabanlı kimlik doğrulama ve rol yetkilendirme.
Kullanıcılar SQLite'da tutulur, Firebase'e de senkronize edilir.
"""

import uuid
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import check_password_hash, generate_password_hash

from database import db

# Firebase kullanıcı senkronizasyonu (isteğe bağlı)
try:
    from firebase_client import push_user, pull_users, push_all_users, push_event
except Exception:
    def push_user(*_, **__):
        pass
    def pull_users():
        return []
    def push_all_users(*_, **__):
        pass
    def push_event(*_, **__):
        pass

# Basit in-memory session store: token -> user dict
SESSIONS = {}


def sync_users_from_firebase():
    """
    Firebase'deki kullanıcıları SQLite'a senkronize et.
    Eğer Firebase'de kullanıcılar varsa ve yerel DB'de yoklarsa ekle.
    Başlangıçta bir kez çağrılır.
    """
    try:
        fb_users = pull_users()
        if not fb_users:
            return

        conn = db.get_connection()
        cursor = conn.cursor()

        for fb_user in fb_users:
            username = fb_user.get("username")
            if not username:
                continue

            # Kullanıcı yerel DB'de var mı kontrol et
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing = cursor.fetchone()

            if not existing:
                pwd_hash = fb_user.get("password_hash") or ""
                if not pwd_hash:
                    print(f"[firebase-sync] Atlandi (sifre yok): {username}")
                    continue
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, is_active)
                    VALUES (?, ?, ?, ?)
                """, (
                    username,
                    pwd_hash,
                    fb_user.get("role", "waiter"),
                    fb_user.get("is_active", 1),
                ))
                print(f"[firebase-sync] Kullanıcı Firebase'den eklendi: {username}")
            else:
                # Mevcut kullanıcıda şifreyi ezme; rol ve aktiflik güncelle
                cursor.execute("""
                    UPDATE users
                    SET role = ?, is_active = ?
                    WHERE username = ?
                """, (
                    fb_user.get("role", "waiter"),
                    fb_user.get("is_active", 1),
                    username,
                ))

        conn.commit()
        conn.close()
        print(f"[firebase-sync] {len(fb_users)} kullanıcı Firebase'den senkronize edildi.")
    except Exception as exc:
        print(f"[firebase-sync] Kullanıcı senkronizasyonu başarısız: {exc}")


def sync_users_to_firebase():
    """
    SQLite'daki tüm kullanıcıları Firebase'e gönder.
    Başlangıçta bir kez çağrılır.
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role, is_active FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()

        push_all_users(users)
        print(f"[firebase-sync] {len(users)} kullanıcı Firebase'e gönderildi.")
    except Exception as exc:
        print(f"[firebase-sync] Firebase'e kullanıcı gönderimi başarısız: {exc}")


def authenticate_user(username, password):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, password_hash, role, is_active
        FROM users
        WHERE username = ?
    """, (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user = dict(row)
    if int(user.get("is_active", 0)) != 1:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None

    # Giriş başarılı — kullanıcı bilgisini Firebase'e de gönder
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE id = ?",
            (user["id"],),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            push_user(dict(row))
        push_event("user.logged_in", {"user_id": user["id"], "username": user["username"]})
    except Exception as exc:
        print(f"[auth] Firebase login sync uyarisi: {exc}")

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }


def create_session(user_dict):
    token = str(uuid.uuid4())
    SESSIONS[token] = user_dict
    return token


def invalidate_session(token):
    if token in SESSIONS:
        del SESSIONS[token]


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token or token not in SESSIONS:
            return jsonify({"success": False, "error": "Yetkisiz erişim"}), 401
        g.current_user = SESSIONS[token]
        g.auth_token = token
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return jsonify({"success": False, "error": "Yetkisiz erişim"}), 401
            if user.get("role") not in roles:
                return jsonify({"success": False, "error": "Bu işlem için yetkiniz yok"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_close_permission(fn):
    """Admin veya ayar açıksa garson masa kapatabilir."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"success": False, "error": "Yetkisiz erişim"}), 401
        if user.get("role") == "admin":
            return fn(*args, **kwargs)
        try:
            from settings_store import get_setting
            if get_setting("waiter_can_close") == "true":
                return fn(*args, **kwargs)
        except Exception:
            pass
        return jsonify({"success": False, "error": "Ödeme alma yetkiniz yok"}), 403
    return wrapper
