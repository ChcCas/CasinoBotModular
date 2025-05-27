import os
from telegram.ext import Application

from modules.db import init_db
from keyboards   import nav_buttons, main_menu   # якщо потрібні в main
from handlers.start import register_start_handler
from handlers.profile import register_profile_handlers

def main():
    init_db()
    app = Application.builder().token(os.getenv("TOKEN")).build()

    register_start_handler(app)
    register_profile_handlers(app)
    # … інші реєстрації …

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path="/webhook",
        webhook_url=os.getenv("WEBHOOK_URL")
    )

if __name__ == "__main__":
    main()
