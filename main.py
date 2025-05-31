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
from modules.handlers.navigation import register_navigation_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("При обробці оновлення трапилася помилка:", exc_info=context.error)

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    # Записуємо global BOT_INSTANCE у modules/config.py:
    import modules.config as config_module
    config_module.BOT_INSTANCE = app.bot

    app.add_error_handler(error_handler)

    # Група 0: /start та всі ConversationHandler-и (адмін, профіль, депозит, виведення)
    register_start_handler(app)
    register_admin_handlers(app)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)

    # Група 1: загальний навігаційний роутер
    register_navigation_handlers(app)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
