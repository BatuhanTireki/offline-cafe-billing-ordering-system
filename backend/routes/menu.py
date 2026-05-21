"""
Menü yönetimi API endpoint'leri
"""
from flask import Blueprint, jsonify, request
from models import MenuModel
from auth import require_auth, require_role

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories():
    """Tüm kategorileri getir"""
    try:
        categories = MenuModel.get_all_categories()
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@menu_bp.route('/categories', methods=['POST'])
@require_auth
@require_role('admin')
def add_category():
    """Yeni kategori ekle"""
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Kategori adı gerekli'}), 400
        
        category_id = MenuModel.add_category(name)
        if category_id:
            return jsonify({'success': True, 'id': category_id})
        return jsonify({'success': False, 'error': 'Kategori eklenemedi'}), 500
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@menu_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_category(category_id):
    """Kategori sil"""
    try:
        if MenuModel.delete_category(category_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Kategori silinemedi'}), 404
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menu_bp.route('/products', methods=['GET'])
@require_auth
def get_products():
    """Tüm ürünleri getir"""
    try:
        products = MenuModel.get_all_products()
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _parse_price(price_raw):
    """Fiyatı parse et ve validate et. Geçerliyse (float, round 2) döner."""
    if price_raw is None:
        return None, 'Fiyat gerekli'
    try:
        price = round(float(price_raw), 2)
    except (TypeError, ValueError):
        return None, 'Geçerli bir fiyat giriniz (örn: 12.50)'
    if price < 0:
        return None, 'Fiyat 0 veya negatif olamaz'
    return price, None

@menu_bp.route('/products', methods=['POST'])
@require_auth
@require_role('admin')
def add_product():
    """Yeni ürün ekle"""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        price_raw = data.get('price')
        category_id = data.get('category_id')
        
        if not name or not category_id:
            return jsonify({'success': False, 'error': 'Tüm alanlar gerekli'}), 400
        
        price, err = _parse_price(price_raw)
        if err:
            return jsonify({'success': False, 'error': err}), 400
        
        product_id = MenuModel.add_product(name, price, int(category_id))
        return jsonify({'success': True, 'id': product_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@menu_bp.route('/products/<int:product_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_product(product_id):
    """Ürün güncelle"""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        price_raw = data.get('price')
        category_id = data.get('category_id')
        
        if not name or not category_id:
            return jsonify({'success': False, 'error': 'Tüm alanlar gerekli'}), 400
        
        price, err = _parse_price(price_raw)
        if err:
            return jsonify({'success': False, 'error': err}), 400
        
        MenuModel.update_product(product_id, name, price, int(category_id))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@menu_bp.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_product(product_id):
    """Ürünü sil"""
    try:
        MenuModel.delete_product(product_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
