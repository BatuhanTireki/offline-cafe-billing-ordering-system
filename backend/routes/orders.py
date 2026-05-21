"""
Sipariş yönetimi API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from models import OrderModel
from auth import require_auth

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/table/<int:table_id>', methods=['GET'])
@require_auth
def get_table_orders(table_id):
    """Masanın siparişlerini getir"""
    try:
        orders = OrderModel.get_table_orders(table_id)
        return jsonify({'success': True, 'data': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _parse_quantity(qty_raw, default=1):
    """Miktarı pozitif integer olarak parse et. default=None ise None/eksik hata döner."""
    if qty_raw is None:
        return (default, None) if default is not None else (None, 'Adet gerekli')
    try:
        q = int(qty_raw)
    except (TypeError, ValueError):
        return None, 'Geçerli adet giriniz (tam sayı)'
    if q < 1:
        return None, 'Adet en az 1 olmalı'
    return q, None

@orders_bp.route('/add', methods=['POST'])
@require_auth
def add_order():
    """Masaya ürün ekle"""
    try:
        data = request.get_json() or {}
        table_id = data.get('table_id')
        product_id = data.get('product_id')
        quantity, err = _parse_quantity(data.get('quantity', 1))
        if err:
            return jsonify({'success': False, 'error': err}), 400
        
        if not table_id or not product_id:
            return jsonify({'success': False, 'error': 'Masa ve ürün ID gerekli'}), 400
        
        result = OrderModel.add_product_to_table(table_id, product_id, quantity)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orders_bp.route('/<int:order_id>/quantity', methods=['PUT'])
@require_auth
def update_quantity(order_id):
    """Sipariş adedini güncelle"""
    try:
        data = request.get_json() or {}
        quantity, err = _parse_quantity(data.get('quantity'), default=None)
        if err or quantity is None:
            return jsonify({'success': False, 'error': err or 'Adet gerekli'}), 400
        
        result = OrderModel.update_order_quantity(order_id, quantity)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@require_auth
def delete_order(order_id):
    """Siparişi sil"""
    try:
        result = OrderModel.remove_order(order_id)
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
