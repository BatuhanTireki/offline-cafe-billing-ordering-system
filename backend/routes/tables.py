"""
Masa yönetimi API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from models import TableModel
from auth import require_auth, require_role

tables_bp = Blueprint('tables', __name__)

@tables_bp.route('/', methods=['GET'])
@require_auth
def get_all_tables():
    """Tüm masaları listele"""
    try:
        tables = TableModel.get_all_tables()
        return jsonify({'success': True, 'data': tables})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@tables_bp.route('/<int:table_id>', methods=['GET'])
@require_auth
def get_table(table_id):
    """Tek masa bilgisi"""
    try:
        table = TableModel.get_table(table_id)
        if table:
            return jsonify({'success': True, 'data': table})
        return jsonify({'success': False, 'error': 'Masa bulunamadı'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@tables_bp.route('/<int:table_id>/open', methods=['POST'])
@require_auth
def open_table(table_id):
    """Masayı aç"""
    try:
        result = TableModel.open_table(table_id)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@tables_bp.route('/<int:table_id>/close', methods=['POST'])
@require_auth
@require_role('admin')
def close_table(table_id):
    """Masayı kapat ve ödeme al"""
    try:
        data = request.get_json()
        payment_method = data.get('payment_method', 'cash')
        
        if payment_method not in ['cash', 'card']:
            return jsonify({'success': False, 'error': 'Geçersiz ödeme yöntemi'}), 400
        
        result = TableModel.close_table(table_id, payment_method)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
