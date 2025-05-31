# modules/db.py

import sqlite3
from sqlite3 import Connection
from typing import Optional, Dict, List
from modules.config import DB_NAME, BOT_INSTANCE
from telegram import ParseMode

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """
    Створює таблиці, якщо їх ще немає:
      - clients(user_id INTEGER PRIMARY KEY, card TEXT UNIQUE, phone TEXT)
      - deposits(...)
      - withdrawals(...)
      - registrations(...)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        user_id INTEGER PRIMARY KEY,
        card    TEXT UNIQUE,
        phone   TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER,
        username       TEXT,
        amount         REAL,
        provider       TEXT,
        payment_method TEXT,
        file_type      TEXT,
        file_id        TEXT,
        timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER,
        username  TEXT,
        amount    REAL,
        method    TEXT,
        details   TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        user_id   INTEGER PRIMARY KEY,
        name      TEXT,
        phone     TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def search_user(query: str) -> Optional[Dict]:
    """
    Шукає клієнта:
    - Якщо query складається лише з цифр і відповідає user_id → шукаємо за user_id.
    - Інакше → шукаємо за card (точна відповідність).
    Повертає словник { 'user_id', 'card', 'phone' } або None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Спроби інтерпретувати як user_id
    if query.isdigit():
        cursor.execute("SELECT user_id, card, phone FROM clients WHERE user_id = ?", (int(query),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    # Інакше шукаємо за карткою
    cursor.execute("SELECT user_id, card, phone FROM clients WHERE card = ?", (query,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def authorize_card(user_id: int, card: str) -> None:
    """
    Додає або оновлює запис user_id → card у clients.
    Якщо запису не було, створюємо. Якщо був — оновлюємо поле card.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM clients WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute(
            "UPDATE clients SET card = ? WHERE user_id = ?",
            (card, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO clients(user_id, card) VALUES (?, ?)",
            (user_id, card)
        )
    conn.commit()
    conn.close()

def get_user_history(user_id: int) -> List[Dict]:
    """
    Повертає список операцій (депозитів та виведень) для конкретного user_id.
    Формує список словників з полями:
      { 'type': 'deposit'/'withdrawal', 'amount':..., 'provider' or 'method':..., 'timestamp':... }
    Обмежимо 10 останніми записами, впорядковано за timestamp DESC.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Обираємо останні 10 депозитів
    cursor.execute("""
      SELECT 'deposit' AS type, amount, provider AS info, timestamp
      FROM deposits
      WHERE user_id = ?
      ORDER BY timestamp DESC
      LIMIT 10
    """, (user_id,))
    deposits = [dict(row) for row in cursor.fetchall()]

    # Обираємо останні 10 виведень
    cursor.execute("""
      SELECT 'withdrawal' AS type, amount, method AS info, timestamp
      FROM withdrawals
      WHERE user_id = ?
      ORDER BY timestamp DESC
      LIMIT 10
    """, (user_id,))
    withdrawals = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Об’єднуємо два списки, сортуємо за timestamp DESC, лишаємо максимум 10 записів
    combined = deposits + withdrawals
    combined.sort(key=lambda x: x["timestamp"], reverse=True)
    return combined[:10]

def broadcast_to_all(text: str) -> None:
    """
    Надсилає text усім user_id із таблиці clients.
    Використовує глобальний BOT_INSTANCE (має бути ініціалізований у main.py).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM clients")
    user_ids = [row["user_id"] for row in cursor.fetchall()]
    conn.close()

    bot = BOT_INSTANCE
    if bot is None:
        return

    for uid in user_ids:
        try:
            bot.send_message(
                chat_id=uid,
                text=text,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            continue
