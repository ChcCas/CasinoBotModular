# src/modules/db.py

import sqlite3
from typing import List, Dict
from modules.config import DB_NAME

def init_db() -> None:
    """
    Ініціалізує базу даних: створює таблиці registrations, deposits, withdrawals.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        name TEXT,
        phone TEXT,
        status TEXT DEFAULT 'pending',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def list_deposits() -> List[Dict]:
    """
    Повертає всі записи про депозити.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, amount FROM deposits ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def list_withdrawals() -> List[Dict]:
    """
    Повертає всі записи про виведення.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, amount FROM withdrawals ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def list_users() -> List[Dict]:
    """
    Повертає всі зареєстровані користувачі (status != 'pending').
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, name, phone 
        FROM registrations 
        WHERE status = 'confirmed'
        ORDER BY id DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def search_user(query: str) -> List[Dict]:
    """
    Шукає користувачів за частиною імені або телефону.
    """
    term = f"%{query}%"
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, name, phone 
        FROM registrations 
        WHERE name LIKE ? OR phone LIKE ?
        ORDER BY id DESC
    """, (term, term))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def broadcast_message(text: str) -> int:
    """
    Повертає кількість користувачів, які отримають розсилку.
    (Фактичну відправку ботом робить хендлер)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM registrations WHERE status = 'confirmed'
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count
