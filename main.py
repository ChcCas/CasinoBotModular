# main.py

import logging
from telegram.ext import ApplicationBuilder, ContextTypes

from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db

from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import profile_conv
from modules.handlers.deposit import deposit_conv
from modules.handlers.withdraw import withdraw_conv
from modules.handlers.registration import registration_conv  # ваш сценарій реєстрації
from modules.handlers.navigation import register_navigation_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def main():
    # 1) Ініціалізуємо базу даних
    init_db()

    # 2) Створюємо Telegram Application
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3) Реєструємо /start та адмін-хендлери
    register_start_handler(app)
    register_admin_handlers(app)

    # 4) Реєструємо ConversationHandler’и (група 0)
    app.add_handler(profile_conv, group=0)
    app.add_handler(deposit_conv, group=0)
    app.add_handler(withdraw_conv, group=0)
    app.add_handler(registration_conv, group=0)
    # (і ще додайте сюди будь-які інші окремі ConversationHandler)

    # 5) Реєструємо загальний роутер (група 1)
    register_navigation_handlers(app)

    # 6) Запускаємо у webhook-режимі
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
