"""
Kimlik doğrulama endpoint'leri
"""
from flask import Blueprint, jsonify, request, g
from werkzeug.security import generate_password_hash

from auth import (
    authenticate_user,
    create_session,
    invalidate_session,
    require_auth,
    require_role,
)
from database import db
from settings_store import get_public_settings

# Firebase push (isteğe bağlı)
try:
    from firebase_client import push_user
except Exception:
    def push_user(*_, **__):
        pass

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"success": False, "error": "Kullanıcı adı ve şifre gerekli"}), 400

        user = authenticate_user(username, password)
        if not user:
            return jsonify({"success": False, "error": "Kullanıcı adı veya şifre hatalı"}), 401

        token = create_session(user)
        return jsonify({
            "success": True,
            "token": token,
            "user": user,
            "settings": get_public_settings(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({
        "success": True,
        "user": g.current_user,
        "settings": get_public_settings(),
    })


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    invalidate_session(g.auth_token)
    return jsonify({"success": True})


@auth_bp.route("/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_users():
    """Tüm kullanıcıları listele (sadece admin)."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, is_active, created_at FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"success": True, "data": users})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/users", methods=["POST"])
@require_auth
@require_role("admin")
def create_user():
    """Yeni kullanıcı oluştur (sadece admin). Firebase'e de senkronize eder."""
    try:
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        role = data.get("role", "waiter")

        if not username or not password:
            return jsonify({"success": False, "error": "Kullanıcı adı ve şifre gerekli"}), 400

        if role not in ("admin", "waiter"):
            return jsonify({"success": False, "error": "Geçersiz rol"}), 400

        conn = db.get_connection()
        cursor = conn.cursor()

        # Kullanıcı adı mevcut mu?
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "error": "Bu kullanıcı adı zaten kullanılıyor"}), 409

        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, 1)
        """, (username, password_hash, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Firebase'e senkronize et
        try:
            push_user({
                "id": user_id,
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "is_active": 1,
            })
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": {"id": user_id, "username": username, "role": role}
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_user(user_id):
    """Kullanıcı güncelle (sadece admin). Firebase'e de senkronize eder."""
    try:
        data = request.get_json() or {}
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Kullanıcı bulunamadı"}), 404

        user = dict(row)
        new_role = data.get("role", user["role"])
        new_active = data.get("is_active", user["is_active"])
        new_password = data.get("password")

        if new_password:
            new_hash = generate_password_hash(new_password)
            cursor.execute("""
                UPDATE users SET password_hash = ?, role = ?, is_active = ? WHERE id = ?
            """, (new_hash, new_role, new_active, user_id))
        else:
            new_hash = user["password_hash"]
            cursor.execute("""
                UPDATE users SET role = ?, is_active = ? WHERE id = ?
            """, (new_role, new_active, user_id))

        conn.commit()
        conn.close()

        # Firebase'e senkronize et
        try:
            push_user({
                "id": user_id,
                "username": user["username"],
                "password_hash": new_hash,
                "role": new_role,
                "is_active": new_active,
            })
        except Exception:
            pass

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_user(user_id):
    """Kullanıcıyı devre dışı bırak (soft delete, sadece admin). Firebase'e de senkronize eder."""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Kullanıcı bulunamadı"}), 404

        user = dict(row)
        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        # Firebase'e devre dışı olarak gönder
        try:
            push_user({
                "id": user_id,
                "username": user["username"],
                "password_hash": user["password_hash"],
                "role": user["role"],
                "is_active": 0,
            })
        except Exception:
            pass

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
