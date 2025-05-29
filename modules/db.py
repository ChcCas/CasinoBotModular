# modules/db.py
import sqlite3
from modules.config import DB_NAME

# Відкриваємо коннекшн у глобальній змінній, щоб не створювати новий кожного разу
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# 1) Міграція: якщо таблиці users не було – створить; 
#    якщо колонка card відсутня – додасть
cursor.execute("PRAGMA table_info(users)")
cols = [row[1] for row in cursor.fetchall()]
if not cols:
    # Таблиці взагалі не існує
    cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT,
        card TEXT,
        is_registered INTEGER DEFAULT 0
    )
    """)
elif 'card' not in cols:
    # Таблиця є, але без card
    cursor.execute("ALTER TABLE users ADD COLUMN card TEXT")

conn.commit()

def get_user(user_id: int) -> dict:
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, phone, card, is_registered
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()
    if not row:
        # новий юзер — створюємо мінімальний запис
        cur.execute("INSERT INTO users(user_id) VALUES(?)", (user_id,))
        conn.commit()
        return {
            'user_id': user_id,
            'username': None,
            'phone': None,
            'card': None,
            'is_registered': 0
        }
    return {
        'user_id':    row[0],
        'username':   row[1],
        'phone':      row[2],
        'card':       row[3],
        'is_registered': row[4]
    }

# …інші функції (save_user, update_user тощо) мають працювати з новим полем card