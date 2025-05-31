# main.py

import logging
from telegram.ext import ApplicationBuilder, ContextTypes

from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db

from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.deposit import register_deposit_handlers
from modules.handlers.withdraw import register_withdraw_handlers
from modules.handlers.registration import register_registration_handlers  # якщо є
from modules.handlers.navigation import register_navigation_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def main():
    # 1. Ініціалізуємо базу даних
    init_db()

    # 2. Створюємо Telegram Application
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3. Регіструємо CommandHandler("/start") і адмін-хендлери (group=0 / group=1)
    register_start_handler(app)
    register_admin_handlers(app)

    # 4. Регіструємо клієнтські ConversationHandler (group=0)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)

    # 5. Опціонально: якщо є сценарій «Реєстрація»
    register_registration_handlers(app)

    # 6. Регіструємо загальний роутер (menu_handler, group=1)
    register_navigation_handlers(app)

    # 7. Запускаємо Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
