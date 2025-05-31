# modules/db.py

import sqlite3
from modules.config import DB_NAME, BOT_INSTANCE

def init_db():
    """
    Створює всі необхідні таблиці у SQLite (clients, deposits, withdrawals, registrations).
    Викликається один раз при запуску бота.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Таблиця клієнтів (в ній зберігаємо user_id, картку та телефон)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            user_id   INTEGER PRIMARY KEY,
            card      TEXT,
            phone     TEXT
        )
        """)

        # Таблиця депозитів
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            username        TEXT,
            amount          REAL,
            provider        TEXT,
            payment_method  TEXT,
            file_type       TEXT,
            file_id         TEXT,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблиця виведень
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

        # Таблиця реєстрацій (якщо потрібна)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            user_id INTEGER PRIMARY KEY,
            name    TEXT,
            phone   TEXT,
            code    TEXT
        )
        """)
        conn.commit()

def search_user(query):
    """
    Шукає клієнта у таблиці clients.
    Аргумент query може бути рядком, який:
      - або приводиться до int і шукається як user_id,
      - або використовується як картка у WHERE card = ?
    Повертає dict із ключами user_id, card, phone або None, якщо не знайдено.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Спроба інтерпретувати query як user_id
        try:
            user_id = int(query)
            cursor.execute("SELECT user_id, card, phone FROM clients WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {"user_id": row[0], "card": row[1], "phone": row[2]}
        except (ValueError, TypeError):
            pass

        # Пошук за номером картки
        cursor.execute("SELECT user_id, card, phone FROM clients WHERE card = ?", (query,))
        row = cursor.fetchone()
        if row:
            return {"user_id": row[0], "card": row[1], "phone": row[2]}

    return None

def authorize_card(user_id, card):
    """
    Зберігає підтверджену картку для клієнта в базі.
    Якщо запис з user_id вже є — оновлює поле card.
    Інакше — створює новий запис.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM clients WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute("UPDATE clients SET card = ? WHERE user_id = ?", (card, user_id))
        else:
            cursor.execute("INSERT INTO clients (user_id, card) VALUES (?, ?)", (user_id, card))
        conn.commit()

def broadcast_to_all(text):
    """
    Розсилка повідомлення text всім користувачам із таблиці clients.
    Використовує глобальний BOT_INSTANCE (створюється у main.py після app = ApplicationBuilder().build()).
    """
    if BOT_INSTANCE is None:
        return

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM clients")
        all_users = cursor.fetchall()

    for (user_id,) in all_users:
        try:
            BOT_INSTANCE.send_message(chat_id=user_id, text=text)
        except Exception:
            # Ігноруємо помилки, наприклад, якщо користувач заблокував бота
            pass
