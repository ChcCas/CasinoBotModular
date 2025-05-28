# main.py

import os
import sqlite3
from telegram.ext import ApplicationBuilder
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.config import TOKEN

# === Ініціалізація БД ===
DB_NAME = "bot_data.db"

with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()

    # Пересоздання таблиці users
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone TEXT,
            card TEXT,
            is_registered INTEGER DEFAULT 0
        )
    """)

    # Таблиця реєстрацій
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблиця поповнень
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            card TEXT,
            provider TEXT,
            payment TEXT,
            file_type TEXT,
            amount TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблиця виведень
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount TEXT,
            method TEXT,
            details TEXT,
            source_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблиця повідомлень (гілки)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
    """)

    conn.commit()

# === Запуск бота ===
app = ApplicationBuilder().token(TOKEN).build()

register_admin_handlers(app)
register_profile_handlers(app)

if __name__ == "__main__":
    app.run_polling()
    app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    url_path="/webhook",
    webhook_url=WEBHOOK_URL,
    open_browser=False  # ← додаємо цю опцію
)