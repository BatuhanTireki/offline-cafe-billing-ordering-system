"""Veritabanı yedekleme ve geri yükleme"""
import os
import shutil
from datetime import datetime
from flask import Blueprint, jsonify, send_file, request
from auth import require_auth, require_role
from database import db

backup_bp = Blueprint("backup", __name__)


def _backup_dir():
    base = os.path.dirname(db.db_path)
    path = os.path.join(base, "backups")
    os.makedirs(path, exist_ok=True)
    return path


@backup_bp.route("/export", methods=["GET"])
@require_auth
@require_role("admin")
def export_backup():
    """Mevcut veritabanının kopyasını indir."""
    try:
        backup_dir = _backup_dir()
        name = f"cafe_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest = os.path.join(backup_dir, name)
        shutil.copy2(db.db_path, dest)
        return send_file(
            dest,
            as_attachment=True,
            download_name=name,
            mimetype="application/octet-stream",
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route("/list", methods=["GET"])
@require_auth
@require_role("admin")
def list_backups():
    try:
        backup_dir = _backup_dir()
        files = []
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith(".db"):
                full = os.path.join(backup_dir, f)
                files.append({
                    "name": f,
                    "size": os.path.getsize(full),
                    "created": datetime.fromtimestamp(os.path.getmtime(full)).isoformat(),
                })
        return jsonify({"success": True, "data": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route("/restore", methods=["POST"])
@require_auth
@require_role("admin")
def restore_backup():
    """Yüklenen .db dosyası ile veritabanını geri yükle."""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "Dosya gerekli"}), 400
        upload = request.files["file"]
        if not upload.filename or not upload.filename.endswith(".db"):
            return jsonify({"success": False, "error": "Geçerli .db dosyası yükleyin"}), 400

        backup_dir = _backup_dir()
        pre_name = f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db.db_path, os.path.join(backup_dir, pre_name))

        temp_path = os.path.join(backup_dir, "_restore_upload.db")
        upload.save(temp_path)
        shutil.copy2(temp_path, db.db_path)
        os.remove(temp_path)

        return jsonify({
            "success": True,
            "message": "Veritabanı geri yüklendi. Değişiklikler için uygulamayı yeniden başlatın.",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
