# main.py

import logging
from telegram.ext import ApplicationBuilder, ContextTypes

from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db

from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers

from modules.handlers.deposit import deposit_conv
from modules.handlers.withdraw import withdraw_conv
from modules.handlers.profile import profile_conv
from modules.handlers.navigation import register_navigation_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def main():
    # 1) Ініціалізуємо БД
    init_db()

    # 2) Створюємо Application
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3) Реєструємо /start та адмін-хендлери
    register_start_handler(app)
    register_admin_handlers(app)

    # 4) Реєструємо ConversationHandler’и і загальний роутер
    #    ВАЖЛИВО: саме в такому порядку і з відповідними групами
    app.add_handler(profile_conv, group=0)
    app.add_handler(deposit_conv, group=0)
    app.add_handler(withdraw_conv, group=0)

    register_navigation_handlers(app)  # це додає menu_router у group=1

    # 5) Налаштовуємо webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
