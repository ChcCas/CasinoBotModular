import os
from telegram.ext import Application

from db import init_db
from modules.config import TOKEN, WEBHOOK_URL, ADMIN_ID, PORT, DB_NAME

from modules.handlers.start        import register_start_handler
from modules.handlers.profile      import register_profile_handlers
from modules.handlers.deposit      import register_deposit_handlers
from modules.handlers.withdraw     import register_withdraw_handlers
from modules.handlers.registration import register_registration_handlers
from modules.handlers.admin        import register_admin_handlers
from modules.handlers.navigation   import register_navigation_handlers  # ← новий імпорт

def main():
    # 1. Ініціалізуємо базу (створимо всі потрібні таблиці)
    init_db(DB_NAME)

    # 2. Створюємо екземпляр бота
    app = Application.builder().token(TOKEN).build()

    # 3. Регіструємо по-модульно всі групи хендлерів
    register_start_handler(app)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)
    register_registration_handlers(app)
    register_admin_handlers(app)

    # 4. Навігація «Назад» і «Головне меню»
    register_navigation_handlers(app)

    # 5. Запускаємо webhook-сервер
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,           # із modules/config.py
        url_path="/webhook", # PTB v22+ вимагає url_path
        webhook_url=WEBHOOK_URL
    )


if __name__ == "__main__":
    main()
