import sqlite3
from modules.config import DB_NAME

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            card    TEXT NOT NULL,
            phone   TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def save_user(user_id: int, card: str, phone: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "REPLACE INTO users (user_id, card, phone) VALUES (?, ?, ?)",
        (user_id, card, phone)
    )
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, card, phone FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row  # None або (user_id, card, phone)
