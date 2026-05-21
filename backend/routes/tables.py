"""
Masa yönetimi API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from models import TableModel
from auth import require_auth, require_role, require_close_permission

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
        if result:
            return jsonify({'success': True})
        return jsonify({
            'success': False,
            'error': 'Masa bulunamadı veya zaten açık'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@tables_bp.route('/<int:table_id>/note', methods=['PUT'])
@require_auth
def update_table_note(table_id):
    """Masa notu güncelle"""
    try:
        data = request.get_json() or {}
        note = data.get('note', '')
        if not TableModel.update_note(table_id, note):
            return jsonify({'success': False, 'error': 'Masa bulunamadı'}), 404
        table = TableModel.get_table(table_id)
        return jsonify({'success': True, 'data': table})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tables_bp.route('/<int:table_id>/transfer', methods=['POST'])
@require_auth
def transfer_table(table_id):
    """Siparişleri başka masaya taşı"""
    try:
        data = request.get_json() or {}
        target_id = data.get('target_table_id')
        if not target_id:
            return jsonify({'success': False, 'error': 'Hedef masa gerekli'}), 400
        ok, err = TableModel.transfer_table(table_id, int(target_id))
        if ok:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': err or 'Transfer başarısız'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tables_bp.route('/<int:table_id>/close', methods=['POST'])
@require_auth
@require_close_permission
def close_table(table_id):
    """Masayı kapat ve ödeme al"""
    try:
        data = request.get_json() or {}
        payment_method = data.get('payment_method', 'cash')
        
        if payment_method not in ['cash', 'card']:
            return jsonify({'success': False, 'error': 'Geçersiz ödeme yöntemi'}), 400
        
        result = TableModel.close_table(table_id, payment_method)
        if result:
            return jsonify({'success': True})
        return jsonify({
            'success': False,
            'error': 'Masa kapatılamadı. Ürün yok veya masa zaten boş.'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
