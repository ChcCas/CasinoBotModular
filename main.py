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

# ─── Налаштування логування ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Глобальний error handler ─────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("При обробці оновлення трапилася помилка:", exc_info=context.error)

def main():
    # 1) Ініціалізуємо БД
    init_db()

    # 2) Створюємо Telegram Application
    app = ApplicationBuilder().token(TOKEN).build()

    # 3) Зберігаємо BOT_INSTANCE для broadcast_to_all
    import modules.config as config_module
    config_module.BOT_INSTANCE = app.bot

    # 4) Додаємо глобальний обробник помилок
    app.add_error_handler(error_handler)

    # 5) Регіструємо /start та адмінські хендлери (група 0)
    register_start_handler(app)
    register_admin_handlers(app)

    # 6) Регіструємо клієнтські ConversationHandler-и (група 0)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)

    # 7) Регіструємо загальний навігаційний роутер (група 1)
    register_navigation_handlers(app)

    # 8) Запускаємо webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
