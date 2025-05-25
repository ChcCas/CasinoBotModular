import logging
from telegram.ext import Application

from modules.constants import TOKEN, ADMIN_ID, DB_NAME
# НЕ імпортуємо setup_handlers зверху!

def main():
    # налаштовуємо логування
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    app = Application.builder().token(TOKEN).build()

    # lazy import, щоб config та constants уже були завантажені
    from modules.handlers import setup_handlers
    setup_handlers(app)

    # запускаємо webhook
    PORT        = int(__import__("os").environ.get("PORT", "8443"))
    WEBHOOK_URL = __import__("os").environ["WEBHOOK_URL"]

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
