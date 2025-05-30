# modules/init_db.py

import sqlite3
from modules.config import DB_NAME

def init_db():
    """
    Ініціалізує базу даних: створює потрібні таблиці, якщо їх ще немає.
    Викликається на старті бота.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблиця для збереження користувачів/клієнтів
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        user_id INTEGER PRIMARY KEY,
        card TEXT,
        phone TEXT,
        confirmed INTEGER DEFAULT 0
    )
    """)

    # Інші таблиці, якщо потрібно:
    # cursor.execute("""CREATE TABLE IF NOT EXISTS deposits (…)""")
    # cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawals (…)""")

    conn.commit()
    conn.close()
