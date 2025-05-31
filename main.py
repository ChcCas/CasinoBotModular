# main.py

import logging
from flask import Flask
from telegram.ext import ApplicationBuilder, ContextTypes

from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db
from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.deposit import register_deposit_handlers
from modules.handlers.withdraw import register_withdraw_handlers
from modules.handlers.navigation import register_navigation_handlers
from register_routes import register_routes  # переконайтеся, що файл register_routes.py знаходиться поруч

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
    app_tg = ApplicationBuilder().token(TOKEN).build()

    # 3) Зберігаємо BOT_INSTANCE для broadcast_to_all
    import modules.config as config_module
    config_module.BOT_INSTANCE = app_tg.bot

    # 4) Додаємо глобальний обробник помилок
    app_tg.add_error_handler(error_handler)

    # 5) Регіструємо /start та адмінські хендлери (group=0)
    register_start_handler(app_tg)
    register_admin_handlers(app_tg)

    # 6) Регіструємо клієнтські ConversationHandler-и (group=0)
    register_profile_handlers(app_tg)
    register_deposit_handlers(app_tg)
    register_withdraw_handlers(app_tg)

    # 7) Регіструємо загальний навігаційний роутер (group=1)
    register_navigation_handlers(app_tg)

    # 8) Створюємо Flask-додаток і реєструємо маршрути
    flask_app = Flask(__name__)
    register_routes(flask_app, app_tg)

    # 9) Запускаємо Flask-сервер
    flask_app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
