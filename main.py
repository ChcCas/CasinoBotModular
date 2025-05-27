# src/main.py

import os
from telegram.ext import Application

from modules.db import init_db
from modules.config import TOKEN, WEBHOOK_URL, ADMIN_ID, PORT
from modules.handlers.start        import register_start_handler
from modules.handlers.profile      import register_profile_handlers
# … інші ваші handlers …

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    register_start_handler(app)
    register_profile_handlers(app)
    # … реєстрація інших handlers …

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
