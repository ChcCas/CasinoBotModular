from telegram.ext import Application
from modules.config import TOKEN, PORT, WEBHOOK_URL
from modules.db import init_db
from modules.handlers.start   import register_start_handler
from modules.handlers.profile import register_profile_handlers
from modules.handlers.deposit import register_deposit_handlers
from modules.handlers.withdraw import register_withdraw_handlers
# … додайте інші handler-и

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    register_start_handler(app)
    register_profile_handlers(app)
    register_deposit_handlers(app)
    register_withdraw_handlers(app)
    # … інші

    app.run_webhook(
        listen="0.0.0.0",
        port=int(PORT),
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
