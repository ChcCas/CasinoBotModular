# src/modules/db.py

import sqlite3
from typing import List, Dict, Optional
from modules.config import DB_NAME


def init_db() -> None:
    """
    Ініціалізує базу даних та створює необхідні таблиці.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблиця реєстрацій користувачів
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        card TEXT,
        phone TEXT,
        status TEXT DEFAULT 'pending',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблиця депозитів
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблиця виведень
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        method TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[Dict]:
    """
    Повертає дані зареєстрованого користувача або None.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, card, phone, status FROM registrations WHERE user_id = ? AND status = 'confirmed'",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_user(user_id: int, card: str, phone: str) -> None:
    """
    Зберігає або оновлює дані користувача та позначає статус 'confirmed'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO registrations (user_id, card, phone, status) VALUES (?, ?, ?, 'confirmed')"
        " ON CONFLICT(user_id) DO UPDATE SET card=excluded.card, phone=excluded.phone, status='confirmed'",
        (user_id, card, phone)
    )
    conn.commit()
    conn.close()


def list_deposits() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, amount FROM deposits ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def list_withdrawals() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, amount, method, details FROM withdrawals ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def list_users() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, card, phone FROM registrations WHERE status = 'confirmed' ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def search_user(query: str) -> List[Dict]:
    term = f"%{query}%"
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, card, phone FROM registrations WHERE card LIKE ? OR phone LIKE ? AND status='confirmed'",
        (term, term)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def broadcast_message(text: str) -> int:
    """
    Повертає кількість підтверджених користувачів для розсилки.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE status='confirmed'")
    count = cursor.fetchone()[0]
    conn.close()
    return count
