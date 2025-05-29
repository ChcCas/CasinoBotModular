import os
import sqlite3
from telegram.ext import ApplicationBuilder

from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.handlers.start import register_start_handler
from modules.handlers.navigation import register_navigation_handlers
from modules.handlers.registration import register_registration_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.deposit import register_deposit_handlers
from modules.handlers.withdraw import register_withdraw_handlers
from modules.handlers.admin import register_admin_handlers

DB_NAME = os.getenv("DB_NAME", "bot_data.db")

# === Ініціалізація БД ===
with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            phone TEXT,
            card TEXT,
            is_registered INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            card TEXT,
            status TEXT DEFAULT 'pending',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
    """)
    conn.commit()

# === Створюємо аплікацію ===
app = ApplicationBuilder().token(TOKEN).build()

# === Регіструємо ВСІ хендлери в порядку:
register_start_handler(app)              # /start  + «🏠 Головне меню»
register_navigation_handlers(app)        # «◀️ Назад» + «🏠 Головне меню»
register_registration_handlers(app)      # кнопка «Реєстрація»
register_profile_handlers(app)           # «Мій профіль» + «Дізнатися картку»
register_deposit_handlers(app)           # «Поповнити»
register_withdraw_handlers(app)          # «Вивід коштів»
register_admin_handlers(app)             # адмін-панель

# === Запуск через Webhook ===
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )