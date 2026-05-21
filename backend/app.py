"""
Ana Flask uygulaması
Offline çalışan REST API sunucusu
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
import logging
import threading
from datetime import datetime

# ---- Dosya tabanlı loglama ----
def _setup_file_logging():
    """Uygulamanın tüm çıktılarını log dosyasına yaz."""
    try:
        if getattr(sys, 'frozen', False):
            log_dir = os.path.join(
                os.environ.get('APPDATA', os.path.dirname(sys.executable)),
                'KafePOS', 'logs'
            )
        else:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'backend.log')

        # Dosya handler
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(handler)

        # print() çıktılarını da yakalayalım
        class LogWriter:
            def __init__(self, original, level):
                self.original = original
                self.level = level
            def write(self, msg):
                if msg.strip():
                    logging.log(self.level, msg.strip())
                if self.original:
                    try:
                        self.original.write(msg)
                        self.original.flush()
                    except Exception:
                        pass
            def flush(self):
                if self.original:
                    try:
                        self.original.flush()
                    except Exception:
                        pass

        sys.stdout = LogWriter(sys.stdout, logging.INFO)
        sys.stderr = LogWriter(sys.stderr, logging.ERROR)

        print(f"[log] Log dosyası: {log_file}")
        print(f"[log] Başlangıç zamanı: {datetime.now().isoformat()}")
        print(f"[log] Python: {sys.version}")
        print(f"[log] Frozen: {getattr(sys, 'frozen', False)}")
        print(f"[log] Executable: {sys.executable}")
        if getattr(sys, '_MEIPASS', None):
            print(f"[log] MEIPASS: {sys._MEIPASS}")
    except Exception as exc:
        # Loglama kurulamazsa sessizce devam et
        print(f"[log] Loglama kurulamadı: {exc}")

_setup_file_logging()

# ---- Ana importlar (log kurulduktan sonra) ----
try:
    from routes import register_routes
    print("[import] routes OK")
except Exception as e:
    print(f"[import] routes HATA: {e}")
    raise

try:
    from firebase_client import get_sync_status, full_sync_from_sqlite, sync_core_to_firestore
    print("[import] firebase_client OK")
except Exception as e:
    print(f"[import] firebase_client HATA: {e}")
    # Firebase import başarısızsa no-op fonksiyonlar kullan
    def get_sync_status():
        return {"enabled": False, "error": str(e)}
    def full_sync_from_sqlite(*_):
        return {"success": False, "error": str(e)}
    def sync_core_to_firestore(*_):
        return {"success": False, "error": str(e)}

try:
    from database import db
    print("[import] database OK")
except Exception as e:
    print(f"[import] database HATA: {e}")
    raise

try:
    from auth import sync_users_from_firebase, sync_users_to_firebase
    print("[import] auth OK")
except Exception as e:
    print(f"[import] auth HATA: {e}")
    def sync_users_from_firebase():
        pass
    def sync_users_to_firebase():
        pass


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
        return jsonify({'status': 'healthy', 'app': 'cafe-pos'})

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


def _background_firebase_sync():
    """
    Firebase kullanıcı senkronizasyonunu arka planda yap.
    Bu fonksiyon Flask başladıktan SONRA daemon thread olarak çalışır,
    böylece Firebase bağlantı sorunları ana sunucuyu bloke etmez.
    """
    try:
        print("[firebase-bg] Arka plan senkronizasyonu başlıyor...")
        sync_users_from_firebase()
        sync_users_to_firebase()
        if os.getenv("FIREBASE_SYNC_CORE_ON_START", "true").lower() == "true":
            result = sync_core_to_firestore(db.get_connection)
            print(f"[firebase-bg] Core sync (products/tables/sales): {result}")
        print("[firebase-bg] Senkronizasyon tamamlandı.")
    except Exception as exc:
        print(f"[firebase-bg] Senkronizasyon hatası (önemsiz): {exc}")


if __name__ == '__main__':
    try:
        # Port kontrolü
        port = find_free_port(5000)
        if port is None:
            print("HATA: Uygun port bulunamadı!", file=sys.stderr)
            sys.exit(1)
        
        print(f"Flask sunucusu başlatılıyor - Port: {port}")
        
        try:
            print(f"[firebase] startup status: {get_sync_status()}")
        except Exception:
            pass

        # Firebase sync'i ARKA PLANDA çalıştır — sunucu başlamasını BLOKE ETME
        def _warmup_firestore():
            try:
                from firebase_client import _get_db, get_sync_status
                _get_db()
                print(f"[firebase] warmup: {get_sync_status()}")
            except Exception as exc:
                print(f"[firebase] warmup hatası: {exc}")

        threading.Thread(target=_warmup_firestore, daemon=True).start()

        sync_thread = threading.Thread(target=_background_firebase_sync, daemon=True)
        sync_thread.start()

        # İsteğe bağlı: full sync de arka planda
        if os.getenv("FIREBASE_FULL_SYNC_ON_START", "false").lower() == "true":
            def _bg_full_sync():
                try:
                    result = full_sync_from_sqlite(db.get_connection)
                    print(f"[firebase-bg] Full sync sonucu: {result}")
                except Exception as exc:
                    print(f"[firebase-bg] Full sync hatası: {exc}")
            threading.Thread(target=_bg_full_sync, daemon=True).start()
        
        app = create_app()
        
        print(f"[server] Flask başlatılıyor http://127.0.0.1:{port}")
        
        # Production modda çalıştır (debug=False)
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            threaded=True
        )
    except Exception as exc:
        print(f"[FATAL] Sunucu başlatılamadı: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
