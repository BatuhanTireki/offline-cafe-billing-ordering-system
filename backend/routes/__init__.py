"""
Routes paketinin init dosyası
"""
from flask import Blueprint

# Blueprint'leri import et
from routes.tables import tables_bp
from routes.menu import menu_bp
from routes.orders import orders_bp
from routes.reports import reports_bp
from routes.sales import sales_bp
from routes.sync import sync_bp
from routes.auth_routes import auth_bp

def register_routes(app):
    """Tüm route'ları uygulamaya kaydet"""
    app.register_blueprint(tables_bp, url_prefix='/api/tables')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
