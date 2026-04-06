"""
Firebase senkron endpoint'leri
"""
from flask import Blueprint, jsonify

from database import db
from firebase_client import full_sync_from_sqlite, get_sync_status
from auth import require_auth, require_role

sync_bp = Blueprint("sync", __name__)


@sync_bp.route("/firebase/status", methods=["GET"])
@require_auth
@require_role("admin")
def firebase_status():
    """Firebase bağlantı durumunu döndür."""
    return jsonify({"success": True, "data": get_sync_status()})


@sync_bp.route("/firebase/full", methods=["POST"])
@require_auth
@require_role("admin")
def firebase_full_sync():
    """SQLite -> Firestore full sync tetikler."""
    result = full_sync_from_sqlite(db.get_connection)
    status = 200 if result.get("success") else 500
    return jsonify(result), status

