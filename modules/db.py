import sqlite3
from modules.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # таблиця користувачів
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id        INTEGER PRIMARY KEY,
            username       TEXT,
            card           TEXT,
            phone          TEXT,
            is_registered  INTEGER DEFAULT 0
        )
    """)

    # таблиці для реєстрацій, депозитів, виведень, ниток навігації
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            name       TEXT,
            phone      TEXT,
            status     TEXT DEFAULT 'pending',
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            card       TEXT,
            provider   TEXT,
            payment    TEXT,
            file_type  TEXT,
            amount     TEXT,
            timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            amount      TEXT,
            method      TEXT,
            details     TEXT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id     INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
    """)

    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, card, phone FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def save_user(user_id: int, card: str, phone: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users(user_id, card, phone, is_registered)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            card=excluded.card,
            phone=excluded.phone,
            is_registered=1
    """, (user_id, card, phone))
    conn.commit()
    conn.close()

def search_user(query: str):
    """
    Шукає користувача за user_id або за номером картки.
    Повертає кортеж із полями з таблиці users, або None, якщо не знайдено.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Припустимо, у вас у таблиці users є поля user_id і card
    cursor.execute(
        "SELECT * FROM users WHERE user_id = ? OR card = ?",
        (query, query)
    )
    row = cursor.fetchone()
    conn.close()
    return row
