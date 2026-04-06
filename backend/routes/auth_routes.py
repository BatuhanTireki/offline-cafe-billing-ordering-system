"""
Kimlik doğrulama endpoint'leri
"""
from flask import Blueprint, jsonify, request, g

from auth import (
    authenticate_user,
    create_session,
    invalidate_session,
    require_auth,
)

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
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"success": True, "user": g.current_user})


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    invalidate_session(g.auth_token)
    return jsonify({"success": True})

