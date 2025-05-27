# src/main.py
import os
from telegram.ext import Application

from modules.db import init_db
from modules.config import TOKEN, WEBHOOK_URL, PORT

# Імпортуємо реєстраційні функції хендлерів з кожного модуля
from modules.handlers.start        import register_start_handler
from modules.handlers.profile      import register_profile_handlers
from modules.handlers.deposit      import register_deposit_handlers
from modules.handlers.withdraw     import register_withdraw_handlers
from modules.handlers.registration import register_registration_handlers
from modules.handlers.admin        import register_admin_handlers
from modules.handlers.navigation   import register_navigation_handlers

def main():
    # Ініціалізуємо базу даних і створюємо всі таблиці
    init_db()

    # Створюємо екземпляр Telegram Application
    app = Application.builder().token(TOKEN).build()

    # Реєструємо усі хендлери
    register_start_handler(app)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)
    register_registration_handlers(app)
    register_admin_handlers(app)
    register_navigation_handlers(app)

    # Запускаємо webhook-сервер
    app.run_webhook(
        listen="0.0.0.0",
        port=int(PORT),          # Порт береться із modules/config.py
        url_path="/webhook",    # PTB v22+ вимагає url_path
        webhook_url=WEBHOOK_URL
    )


if __name__ == "__main__":
    main()
