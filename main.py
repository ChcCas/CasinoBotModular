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
from modules.handlers.registration import registration_conv
from modules.handlers.admin import (
    admin_search_conv,
    admin_broadcast_conv,
    show_admin_panel  # якщо десь потребується
)
from modules.handlers.navigation import register_navigation_handlers

# ─── Налаштування логування ───────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def main():
    # 1) ініціалізуємо БД
    init_db()

    # 2) створюємо Application
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 3) Реєструємо /start та адмінські хендлери, що не вимагають розмов
    register_start_handler(app)
    # Реєструємо show_admin_panel (callback admin_panel):
    # відпрацює, якщо жоден група 0 його не «пощупала».
    register_admin_handlers(app)

    # 4) Регіструємо всі ConversationHandler’и у групі 0 (пріоритетніше за menu_router)
    app.add_handler(profile_conv, group=0)
    app.add_handler(deposit_conv, group=0)
    app.add_handler(withdraw_conv, group=0)
    app.add_handler(registration_conv, group=0)

    # Адмінські ConversationHandler’и (пошук і розсилка)
    app.add_handler(admin_search_conv, group=0)
    app.add_handler(admin_broadcast_conv, group=0)

    # 5) Нарешті додаємо загальний router у групі 1
    register_navigation_handlers(app)

    # 6) Запускаємо Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
