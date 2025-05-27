# db.py
import sqlite3
from modules.config import DB_NAME

def init_db():
    """Створює файл БД і всі необхідні таблиці, якщо їх ще немає."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Таблиця користувачів: для збереження card і phone
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id   INTEGER PRIMARY KEY,
        card      TEXT    NOT NULL,
        phone     TEXT    NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: int):
    """Повертає (user_id, card, phone) або None."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, card, phone FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def upsert_user(user_id: int, card: str, phone: str):
    """Вставляє/оновлює record користувача."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users(user_id, card, phone)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
      card  = excluded.card,
      phone = excluded.phone
    """, (user_id, card, phone))
    conn.commit()
    conn.close()
