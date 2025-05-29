import sqlite3
from typing import Optional, Tuple
from modules.config import DB_NAME

def init_db() -> None:
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            user_id    INTEGER PRIMARY KEY,
            card       TEXT,
            phone      TEXT,
            authorized INTEGER DEFAULT 0
        )""")
        conn.commit()

def get_user(user_id: int) -> Optional[Tuple[int,str,str]]:
    """
    Повертає (user_id, card, phone) якщо є авторизація,
    або None.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, card, phone FROM clients WHERE user_id = ? AND authorized = 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else None

def save_user(user_id: int, card: str, phone: str) -> None:
    """
    Зберігає/онновлює клієнта як авторизованого.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients(user_id, card, phone, authorized)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            card=excluded.card, phone=excluded.phone, authorized=1
    """, (user_id, card, phone))
    conn.commit()
    conn.close()