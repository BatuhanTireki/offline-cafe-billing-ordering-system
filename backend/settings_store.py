"""
Uygulama ayarları (SQLite settings tablosu).
"""

from database import db

DEFAULTS = {
    "waiter_can_close": "false",
}


def get_setting(key: str, default=None) -> str:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return DEFAULTS.get(key, default if default is not None else "")


def set_setting(key: str, value: str) -> None:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()


def get_all_settings() -> dict:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = {r["key"]: r["value"] for r in cursor.fetchall()}
    conn.close()
    result = dict(DEFAULTS)
    result.update(rows)
    return result


def get_public_settings() -> dict:
    """Giriş yapmış tüm kullanıcılar için görünür ayarlar."""
    return {
        "waiter_can_close": get_setting("waiter_can_close") == "true",
    }
