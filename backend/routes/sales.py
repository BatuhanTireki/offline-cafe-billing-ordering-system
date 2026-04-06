"""
Satış geçmişi API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from database import db
from auth import require_auth, require_role

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/history', methods=['GET'])
@require_auth
@require_role('admin')
def get_sales_history():
    """Tarih aralığına göre satış geçmişi"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Tarih aralığı gerekli'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                table_number,
                total_amount,
                payment_method,
                sale_date,
                opened_at,
                closed_at
            FROM completed_sales
            WHERE DATE(sale_date) BETWEEN ? AND ?
            ORDER BY sale_date DESC
        """, (start_date, end_date))
        
        sales = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'data': sales})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sales_bp.route('/<int:sale_id>/details', methods=['GET'])
@require_auth
@require_role('admin')
def get_sale_details(sale_id):
    """Tek satışın detayları"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Satış bilgisi
        cursor.execute("""
            SELECT * FROM completed_sales WHERE id = ?
        """, (sale_id,))
        sale = cursor.fetchone()
        
        if not sale:
            conn.close()
            return jsonify({'success': False, 'error': 'Satış bulunamadı'}), 404
        
        # Satış detayları
        cursor.execute("""
            SELECT * FROM sale_details WHERE sale_id = ?
        """, (sale_id,))
        details = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        result = dict(sale)
        result['details'] = details
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
