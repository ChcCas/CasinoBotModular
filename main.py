import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from modules.config import TOKEN, WEBHOOK_URL, PORT, ADMIN_ID

from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.navigation import register_navigation_handlers

# === Налаштування логування ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Глобальний обробник помилок ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)
    # Опційно: повідомити адміну про помилку
    # await context.bot.send_message(chat_id=ADMIN_ID,
    #                                text=f"⚠️ Помилка: {context.error}")

# === Міграція та ініціалізація БД ===
DB_NAME = "bot_data.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# Перевіряємо, чи існує таблиця users і колонка card
cursor.execute("PRAGMA table_info(users)")
cols = [row[1] for row in cursor.fetchall()]
if not cols:
    # Створюємо таблицю з усіма полями
    cursor.execute("""
        CREATE TABLE users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            phone        TEXT,
            card         TEXT,
            is_registered INTEGER DEFAULT 0
        )
    """)
elif 'card' not in cols:
    # Додаємо колонку card
    cursor.execute("ALTER TABLE users ADD COLUMN card TEXT")

# Інші таблиці
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

# === Створення Telegram-додатку ===
app = ApplicationBuilder().token(TOKEN).build()

# Реєструємо обробник помилок
app.add_error_handler(error_handler)

# === Реєстрація хендлерів ===
register_start_handler(app)
register_admin_handlers(app)
register_profile_handlers(app)
register_navigation_handlers(app)

# === Запуск через webhook ===
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )