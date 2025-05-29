# modules/db.py
import sqlite3
from typing import List, Dict, Optional
from modules.config import DB_NAME

def init_db() -> None:
    """Створює всі необхідні таблиці, якщо їх ще немає."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            card TEXT,
            phone TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            card TEXT,
            provider TEXT,
            payment TEXT,
            amount REAL,
            file_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            method TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()

def get_user(user_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    row = conn.cursor().execute(
        "SELECT user_id, card, phone, status FROM registrations WHERE user_id = ? AND status = 'confirmed'",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def save_user(user_id: int, card: str, phone: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "INSERT INTO registrations (user_id, card, phone, status) VALUES (?, ?, ?, 'confirmed') "
        "ON CONFLICT(user_id) DO UPDATE SET card=excluded.card, phone=excluded.phone, status='confirmed'",
        (user_id, card, phone)
    )
    conn.commit()
    conn.close()

def list_deposits() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.cursor().execute(
        "SELECT id, user_id, amount FROM deposits ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_withdrawals() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.cursor().execute(
        "SELECT id, user_id, amount, method, details FROM withdrawals ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def list_users() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.cursor().execute(
        "SELECT user_id, card, phone FROM registrations WHERE status = 'confirmed' ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_user(query: str) -> List[Dict]:
    term = f"%{query}%"
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.cursor().execute(
        "SELECT user_id, card, phone FROM registrations "
        "WHERE (card LIKE ? OR phone LIKE ?) AND status='confirmed'",
        (term, term)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def broadcast_message(text: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM registrations WHERE status='confirmed'")
    count = cur.fetchone()[0]
    conn.close()
    return count