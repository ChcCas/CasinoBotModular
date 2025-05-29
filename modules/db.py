# modules/db.py

import sqlite3
from modules.config import DB_NAME

# Відкриваємо єдине з’єднання до БД
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# === Міграція / створення таблиці users ===
cursor.execute("PRAGMA table_info(users)")
user_cols = [row[1] for row in cursor.fetchall()]

if not user_cols:
    # Таблиці зовсім немає — створюємо з нуля
    cursor.execute("""
        CREATE TABLE users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            phone         TEXT,
            card          TEXT,
            is_registered INTEGER DEFAULT 0
        )
    """)
elif 'card' not in user_cols:
    # Таблиця є, але без поля card — додаємо колонку
    cursor.execute("ALTER TABLE users ADD COLUMN card TEXT")

# === Створення інших таблиць (якщо їх нема) ===
cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        name       TEXT,
        phone      TEXT,
        card       TEXT,
        status     TEXT DEFAULT 'pending',
        timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        username   TEXT,
        card       TEXT,
        provider   TEXT,
        payment    TEXT,
        file_type  TEXT,
        amount     TEXT,
        timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        username    TEXT,
        amount      TEXT,
        method      TEXT,
        details     TEXT,
        source_code TEXT,
        timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS threads (
        user_id     INTEGER PRIMARY KEY,
        base_msg_id INTEGER
    )
""")

conn.commit()

# === Функції для роботи з БД ===

def get_user(user_id: int) -> dict:
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, phone, card, is_registered
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    if not row:
        # Якщо нового юзера ще немає — створюємо базовий запис
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (user_id,))
        conn.commit()
        return {'user_id': user_id, 'username': None, 'phone': None, 'card': None, 'is_registered': 0}
    return {
        'user_id':      row[0],
        'username':     row[1],
        'phone':        row[2],
        'card':         row[3],
        'is_registered': row[4],
    }

def save_user(user: dict):
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET username = ?, phone = ?, card = ?, is_registered = ?
        WHERE user_id = ?
    """, (
        user.get('username'),
        user.get('phone'),
        user.get('card'),
        user.get('is_registered'),
        user['user_id']
    ))
    conn.commit()

def list_deposits() -> list:
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, username, card, provider, payment, file_type, amount, timestamp
        FROM deposits
        ORDER BY timestamp DESC
    """)
    return cur.fetchall()

def list_withdrawals() -> list:
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, username, amount, method, details, source_code, timestamp
        FROM withdrawals
        ORDER BY timestamp DESC
    """)
    return cur.fetchall()

def list_users() -> list:
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, phone, card, is_registered
        FROM users
        ORDER BY user_id
    """)
    return cur.fetchall()

def search_user(keyword: str) -> list:
    cur = conn.cursor()
    term = f"%{keyword}%"
    cur.execute("""
        SELECT user_id, username, phone, card, is_registered
        FROM users
        WHERE username LIKE ? OR phone LIKE ? OR card LIKE ?
    """, (term, term, term))
    return cur.fetchall()

def broadcast_message(text: str) -> list:
    """
    Повертає список всіх user_id,
    щоб хендлер розіслав їм повідомлення.
    """
    return [row[0] for row in list_users()]