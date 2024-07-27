import sqlite3
import json
from pages_util.theme_utils import dracula_soft_dark


def init_db():
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    conn.close()


def save_theme(theme):
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("theme", json.dumps(theme)),
    )
    conn.commit()
    conn.close()


def load_theme():
    conn = sqlite3.connect("settings.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='theme'")
    result = c.fetchone()
    conn.close()
    if result:
        return json.loads(result[0])
    return dracula_soft_dark  # Default theme if no theme is saved
