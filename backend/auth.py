"""
Basit token tabanlı kimlik doğrulama ve rol yetkilendirme.
"""

import uuid
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import check_password_hash

from database import db

# Basit in-memory session store: token -> user dict
SESSIONS = {}


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

