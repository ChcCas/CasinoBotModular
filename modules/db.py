import sqlite3
import os
from modules.config import DB_NAME, BOT_INSTANCE
from datetime import datetime

# Якщо треба створити відповідні таблиці, робимо це тут:
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Таблиця клієнтів: user_id (prime key), card, created_at
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            user_id   INTEGER PRIMARY KEY,
            card      TEXT,
            created_at TEXT
        )
    """)
    # Таблиця транзакцій (безпечний приклад)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            type       TEXT,           -- "deposit" або "withdraw"
            amount     REAL,
            info       TEXT,           -- провайдер або реквізит
            timestamp  TEXT
        )
    """)
    conn.commit()
    conn.close()

# Повертає рядок (або dict) із записом користувача (з таблиці clients), якщо знайдено:
def search_user(query: str):
    """
    Можливі варіанти:
      - query рівний user_id ( рядок числа ) → шукаємо по user_id
      - query рівний card (текст картки) → шукаємо по карті
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Якщо query складається тільки з цифр і довжина більше 4,
    # можемо спробувати трактувати як картку, але перевірку робимо універсально:
    cursor.execute("""
        SELECT user_id, card, created_at
          FROM clients
         WHERE user_id = ?
            OR card = ?
    """, (query, query))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"user_id": row[0], "card": row[1], "created_at": row[2]}
    else:
        return None

def authorize_card(user_id: int, card: str):
    """
    Якщо user_id вже є в таблиці, оновлюємо поле card;
    якщо нема — створюємо новий запис.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    # Перевіримо, чи є такий user_id
    cursor.execute("SELECT user_id FROM clients WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("UPDATE clients SET card = ?, created_at = ? WHERE user_id = ?",
                       (card, now, user_id))
    else:
        cursor.execute("INSERT INTO clients (user_id, card, created_at) VALUES (?, ?, ?)",
                       (user_id, card, now))
    conn.commit()
    conn.close()

def get_user_history(user_id: int, limit: int = 10):
    """
    Повертає до `limit` останніх транзакцій користувача.
    Повертає список dict-ів:
      [{ "type": "deposit",  "amount": 100.0, "info": "СТАРА СИСТЕМА", "timestamp": "..."},
       { "type": "withdraw", "amount": 50.0,  "info": "Карта 1234...",      "timestamp": "..."} 
      ]
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, amount, info, timestamp
          FROM transactions
         WHERE user_id = ?
      ORDER BY id DESC
         LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()

    lst = []
    for r in rows:
        lst.append({"type": r[0], "amount": r[1], "info": r[2], "timestamp": r[3]})
    return lst

# (За бажанням) функція broadcast_to_all, яка надсилає повідомлення
# усім користувачам із таблиці clients.
# Для прикладу:
def broadcast_to_all(text: str):
    """
    Надсилає текст всім user_id із таблиці clients.
    Працює лише якщо в modules.config.BOT_INSTANCE вже лежить Telegram-бот.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM clients")
    rows = cursor.fetchall()
    conn.close()

    for (user_id,) in rows:
        try:
            BOT_INSTANCE.send_message(chat_id=user_id, text=text)
        except Exception:
            pass
