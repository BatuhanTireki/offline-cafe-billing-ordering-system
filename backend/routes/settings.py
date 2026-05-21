"""Uygulama ayarları API"""
from flask import Blueprint, jsonify, request, g
from auth import require_auth, require_role
from settings_store import get_all_settings, get_public_settings, set_setting

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET"])
@require_auth
def get_settings():
    user_role = g.current_user.get("role")
    if user_role == "admin":
        return jsonify({"success": True, "data": get_all_settings()})
    return jsonify({"success": True, "data": get_public_settings()})


@settings_bp.route("/", methods=["PUT"])
@require_auth
@require_role("admin")
def update_settings():
    data = request.get_json() or {}
    if "waiter_can_close" in data:
        val = "true" if data["waiter_can_close"] in (True, "true", 1, "1") else "false"
        set_setting("waiter_can_close", val)
    return jsonify({"success": True, "data": get_public_settings()})
