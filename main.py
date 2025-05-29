import os
import sqlite3
from telegram.ext import ApplicationBuilder

from modules.config               import TOKEN, WEBHOOK_URL, PORT, DB_NAME
from modules.db                   import init_db   # нова ініціалізація
from modules.handlers.start       import register_start_handler
from modules.handlers.admin       import register_admin_handlers
from modules.handlers.profile     import register_profile_handlers
from modules.handlers.navigation  import register_navigation_handlers
from modules.handlers.deposit     import register_deposit_handlers
from modules.handlers.withdraw    import register_withdraw_handlers
from modules.handlers.registration import register_registration_handlers

# якщо ти ще мав якісь інші таблиці — ініціалізуй їх тут
init_db()

# === Запуск бота ===
app = ApplicationBuilder().token(TOKEN).build()

# Реєструємо усі flow
register_start_handler(app)
register_navigation_handlers(app)      # обробляє ◀️Назад і 🏠Головне меню
register_profile_handlers(app)         # "Мій профіль"
register_deposit_handlers(app)         # "DEPOSIT_START" → поповнення
register_withdraw_handlers(app)        # "WITHDRAW_START" → виведення
register_registration_handlers(app)    # "register" → реєстрація
register_admin_handlers(app)           # адмін-панель

if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )