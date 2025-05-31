# modules/db.py

import sqlite3
from modules.config import DB_NAME

def init_db():
    """
    Ініціалізує базу: створює необхідні таблиці, якщо їх ще немає.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблиця для профілю (клієнти)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        user_id INTEGER PRIMARY KEY,
        card TEXT,
        phone TEXT,
        confirmed INTEGER DEFAULT 0
    )
    """)

    # Таблиця депозитів (за потребою)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        card TEXT,
        provider TEXT,
        payment TEXT,
        amount REAL,
        file_type TEXT
    )
    """)

    # Таблиця виведень (за потребою)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        method TEXT,
        details TEXT,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()

def search_user(query: str):
    """
    Шукає користувача за user_id або за номером картки.
    Повертає dict із полями (user_id, card, phone, confirmed) або None.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, card, phone, confirmed FROM clients WHERE user_id = ? OR card = ?",
        (query, query)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "card": row[1],
            "phone": row[2],
            "confirmed": row[3]
        }
    return None

def list_all_clients():
    """
    Повертає весь список user_id з clients, у яких confirmed = 1.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM clients WHERE confirmed = 1")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def authorize_card(user_id: int, card: str, phone: str = None):
    """
    Підтверджуємо картку клієнта (установлюємо confirmed=1).
    Якщо запису не було, створюємо його, інакше оновлюємо.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (user_id, card, phone, confirmed)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            card = excluded.card,
            phone = COALESCE(excluded.phone, clients.phone),
            confirmed = 1
    """, (user_id, card))
    conn.commit()
    conn.close()
