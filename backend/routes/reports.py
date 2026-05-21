"""
Raporlama API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from models import ReportModel
from datetime import datetime
from auth import require_auth, require_role

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_role('admin')
def get_dashboard():
    """Canlı dashboard özeti"""
    try:
        from models import ReportModel
        data = ReportModel.get_dashboard()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@reports_bp.route('/daily', methods=['GET'])
@require_auth
@require_role('admin')
def get_daily_report():
    """Günlük rapor"""
    try:
        date = request.args.get('date')  # YYYY-MM-DD formatında
        report = ReportModel.get_daily_sales(date)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/range', methods=['GET'])
@require_auth
@require_role('admin')
def get_range_report():
    """Tarih aralığı raporu"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Başlangıç ve bitiş tarihi gerekli'}), 400
        
        report = ReportModel.get_sales_by_date_range(start_date, end_date)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
