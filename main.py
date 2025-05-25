import os
from telegram.ext import Application
# ← ось тут імпорт із config.py, а не constants.py
from modules.config    import TOKEN, ADMIN_ID, DB_NAME
from modules.handlers  import setup_handlers

TOKEN       = os.environ["TOKEN"]        # якщо ви зберігаєте токен у .env
PORT        = int(os.environ.get("PORT","8443"))
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

def main():
    app = Application.builder().token(TOKEN).build()
    setup_handlers(app)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()