import logging
from telegram.ext import ApplicationBuilder, ContextTypes
from modules.config import TOKEN, WEBHOOK_URL, PORT
from modules.db import init_db
from modules.handlers.start import register_start_handler
from modules.handlers.admin import register_admin_handlers
from modules.handlers.profile import register_profile_handlers
from modules.handlers.navigation import register_navigation_handlers

# налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# глобальний error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def main():
    # 1) ініціалізуємо БД
    init_db()

    # 2) створюємо бот
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3) реєструємо хендлери
    register_start_handler(app)
    register_admin_handlers(app)
    register_profile_handlers(app)
    register_navigation_handlers(app)

    # 4) запускаємо webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
