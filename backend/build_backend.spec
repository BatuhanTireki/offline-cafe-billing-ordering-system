# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec dosyası
Backend'i tek exe dosyasına paketler
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# ---- Firebase Admin SDK ve bağımlılıkları (otomatik topla) ----
firebase_datas, firebase_binaries, firebase_hiddenimports = [], [], []
for pkg in [
    'firebase_admin',
    'google.cloud.firestore',
    'google.cloud.firestore_v1',
    'google.api_core',
    'google.auth',
    'google.oauth2',
    'grpc',
    'google.protobuf',
]:
    try:
        d, b, h = collect_all(pkg)
        firebase_datas += d
        firebase_binaries += b
        firebase_hiddenimports += h
    except Exception:
        pass

# Ek hidden import'lar (collect_all'ın kaçırabileceği modüller)
extra_hiddenimports = [
    'proto',
    'proto.marshal',
    'proto.marshal.rules',
    'proto.marshal.rules.dates',
    'proto.marshal.rules.wrappers',
    'proto.marshal.rules.struct',
    'proto.marshal.rules.enums',
    'proto.marshal.rules.message',
    'cachetools',
    'certifi',
    'charset_normalizer',
    'httplib2',
    'idna',
    'pyasn1',
    'pyasn1.type',
    'pyasn1.codec',
    'pyasn1.codec.der',
    'pyasn1.codec.native',
    'pyasn1_modules',
    'rsa',
    'requests',
    'urllib3',
    'flask',
    'flask_cors',
    'werkzeug',
    'werkzeug.security',
    'jinja2',
    'markupsafe',
    'click',
    'itsdangerous',
    'blinker',
]

# firebase-service-account.json varsa datas'a ekle
extra_datas = []
if os.path.isfile('firebase-service-account.json'):
    extra_datas.append(('firebase-service-account.json', '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=firebase_binaries,
    datas=extra_datas + firebase_datas,
    hiddenimports=firebase_hiddenimports + extra_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='cafe_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console göster (hata ayıklama için)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
