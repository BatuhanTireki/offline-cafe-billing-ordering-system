"""
Ana Flask uygulaması
Offline çalışan REST API sunucusu
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Route'ları import et
from routes import register_routes
from firebase_client import get_sync_status, full_sync_from_sqlite
from database import db

def create_app():
    """Flask uygulamasını oluştur ve yapılandır"""
    app = Flask(__name__)
    
    # CORS ayarları - Electron'dan gelen isteklere izin ver
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Ana endpoint
    @app.route('/')
    def index():
        return jsonify({
            'status': 'online',
            'message': 'Kafe POS Backend çalışıyor',
            'version': '1.0.0'
        })
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy'})

    @app.route('/firebase-health')
    def firebase_health():
        """Firebase bağlantı durumunu göster (debug)."""
        return jsonify({'success': True, 'data': get_sync_status()})
    
    # Route'ları kaydet
    register_routes(app)
    
    return app

def find_free_port(start_port=5000, max_attempts=10):
    """Boş port bul"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

if __name__ == '__main__':
    # Port kontrolü
    port = find_free_port(5000)
    if port is None:
        print("HATA: Uygun port bulunamadı!", file=sys.stderr)
        sys.exit(1)
    
    print(f"Flask sunucusu başlatılıyor - Port: {port}")
    print(f"[firebase] startup status: {get_sync_status()}")

    # İsteğe bağlı: uygulama açılışında full sync
    if os.getenv("FIREBASE_FULL_SYNC_ON_START", "false").lower() == "true":
        result = full_sync_from_sqlite(db.get_connection)
        print(f"[firebase] startup full sync sonucu: {result}")
    
    app = create_app()
    
    # Production modda çalıştır (debug=False)
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        threaded=True
    )
