# modules/db.py

import sqlite3
from modules.config import DB_NAME

# Відкриваємо єдине з’єднання
conn = sqlite3.connect(DB_NAME, check_same_thread=False)

def get_user(user_id: int) -> dict:
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, phone, card, is_registered
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    if not row:
        # Якщо немає — створюємо базовий запис
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
    щоб у адміністратора була можливість розіслати їм повідомлення.
    """
    users = list_users()
    return [row[0] for row in users]