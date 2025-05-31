# modules/db.py

import sqlite3
from typing import Optional, Dict, List
from modules.config import DB_NAME, BOT_INSTANCE

def init_db() -> None:
    """
    Ініціалізує базу даних, створює необхідні таблиці, якщо їх ще не існує:
      1) clients — для авторизації (зберігає user_id, card, phone, created_at).
      2) deposits — для збереження інформації про поповнення.
      3) withdrawals — для збереження інформації про виведення.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1) Таблиця clients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            user_id    INTEGER PRIMARY KEY,
            card       TEXT UNIQUE,
            phone      TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2) Таблиця deposits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            provider    TEXT,
            payment_method TEXT,
            amount      REAL,
            file_type   TEXT,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES clients(user_id)
        )
    """)

    # 3) Таблиця withdrawals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            method      TEXT,
            details     TEXT,
            amount      REAL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES clients(user_id)
        )
    """)

    conn.commit()
    conn.close()


def search_user(query: str) -> Optional[Dict]:
    """
    Шукає користувача за:
     - user_id (якщо query — ціле число), або
     - card (якщо query — рядок, що не перетворюється в int).

    Повертає словник з усіма полями із таблиці clients, якщо запис знайдено.
    Інакше — повертає None.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Якщо query можна перетворити на int, шукаємо по user_id
    try:
        uid = int(query)
        cursor.execute("SELECT * FROM clients WHERE user_id = ?", (uid,))
    except ValueError:
        # Якщо не integer, шукаємо по картці
        cursor.execute("SELECT * FROM clients WHERE card = ?", (query,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Перетворюємо sqlite3.Row у звичайний dict
    return {key: row[key] for key in row.keys()}


def authorize_card(user_id: int, card: str) -> None:
    """
    «Авторизує» картку для даного користувача:
     - Якщо в таблиці clients для цього user_id уже є запис — оновлює поле card.
     - Якщо користувача ще немає — створює новий рядок з user_id і card.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Використовуємо INSERT OR REPLACE, щоб або вставити, або замінити існуючий record
    cursor.execute(
        "INSERT OR REPLACE INTO clients (user_id, card) VALUES (?, ?)",
        (user_id, card)
    )
    conn.commit()
    conn.close()


def get_user_history(user_id: int) -> List[Dict]:
    """
    Повертає до 10 останніх операцій (депозитів + виведень) для даного user_id
    у хронологічному порядку (найновіші зверху).
    Кожен елемент списку — дикт з полями:
      - type: "deposit" або "withdraw"
      - info: назва провайдера (для депозитів) або метод (для виведень)
      - amount: сума
      - timestamp: час транзакції
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            'deposit' AS type,
            provider AS info,
            amount,
            timestamp
        FROM deposits
        WHERE user_id = ?
        UNION ALL
        SELECT
            'withdraw' AS type,
            method AS info,
            amount,
            timestamp
        FROM withdrawals
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user_id, user_id))

    rows = cursor.fetchall()
    conn.close()

    return [{key: row[key] for key in row.keys()} for row in rows]


def broadcast_to_all(text: str) -> None:
    """
    Відправляє текстову розсилку всім user_id, що збережені у таблиці clients.
    Використовує глобальний BOT_INSTANCE (збережений у modules/config.py).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM clients")
    all_users = cursor.fetchall()
    conn.close()

    for (uid,) in all_users:
        try:
            BOT_INSTANCE.send_message(chat_id=uid, text=text)
        except Exception:
            # Якщо, наприклад, користувач заблокував бота, просто ігноруємо
            continue
