# main.py

import logging
from telegram.ext import ApplicationBuilder, ContextTypes
from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db
from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.navigation import register_navigation_handlers

# ─── Налаштування логування ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Глобальний error handler ─────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

# ─── Точка входу ────────────────────────────────────────────────────────────────
def main():
    # 1) Ініціалізуємо базу даних (створюємо таблиці, якщо їх немає)
    init_db()

    # 2) Створюємо Telegram Application із токеном
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3) Реєструємо всі наші хендлери
    register_start_handler(app)
    register_admin_handlers(app)
    register_profile_handlers(app)
    register_navigation_handlers(app)

    # 4) Запускаємо бот у режимі webhook
    #    - listen: IP-адреса, на якій Flask-сервер слухає вхідні з’єднання
    #    - port: порт, по якому Render (або інший хостинг) пробросить трафік
    #    - url_path: шлях для POST-запитів від Telegram (має співпадати з WEBHOOK_URL)
    #    - webhook_url: публічний URL, куди Telegram надсилатиме оновлення
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
