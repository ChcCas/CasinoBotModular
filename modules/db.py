# modules/db.py

import sqlite3
from modules.config import DB_NAME

def init_db():
    """
    Створює всі необхідні таблиці, якщо їх ще немає.
    Викликається перед запуском бота.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Таблиця користувачів: в ній зберігатимемо user_id, картку, телефон тощо
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
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            username      TEXT,
            amount        REAL,
            provider      TEXT,
            payment_method TEXT,
            file_type     TEXT,
            file_id       TEXT,
            timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Таблиця виведень
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            username     TEXT,
            amount       REAL,
            method       TEXT,
            details      TEXT,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
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
    Шукає клієнта за user_id або за текстом картки.
    Якщо знайдено — повертає словник або кортеж із даними клієнта.
    Якщо не знайдено — повертає None.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Спробуємо інтерпретувати як user_id (ціле число)
        try:
            user_id = int(query)
            cursor.execute("SELECT user_id, card, phone FROM clients WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {"user_id": row[0], "card": row[1], "phone": row[2]}
        except ValueError:
            pass

        # Якщо не числа, пошук за карткою
        cursor.execute("SELECT user_id, card, phone FROM clients WHERE card = ?", (query,))
        row = cursor.fetchone()
        if row:
            return {"user_id": row[0], "card": row[1], "phone": row[2]}

    return None

def authorize_card(user_id, card):
    """
    Зберігає підтверджену картку для клієнта в базі.
    Якщо у таблиці clients вже є запис з цим user_id, оновлює поле card.
    Інакше — створює новий.
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
    Простий приклад функції для розсилки всім користувачам.
    Витягує всі chat_id з таблиці clients і надсилає кожному текст.
    (У разі великої кількості користувачів зробіть batch-розсилку.)
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM clients")
        all_users = cursor.fetchall()

    # Передбачимо, що у нас є глобальний обʼєкт `bot` (можна імпортувати з main або з контексту),
    # але зазвичай ми будемо викликати цю функцію з хендлера, у якому є context.bot.
    # Нижче — простий приклад, але зазвичай краще робити асинхронну розсилку:
    for (user_id,) in all_users:
        try:
            # Тут просто використовуємо Bot API напряму:
            from modules.config import BOT_INSTANCE
            BOT_INSTANCE.send_message(chat_id=user_id, text=text)
        except Exception:
            # Ігноруємо помилки (якщо юзер заблокував бота тощо)
            pass
