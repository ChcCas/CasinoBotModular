import os
from telegram.ext import Application
from modules.handlers import setup_handlers

TOKEN = os.environ["TOKEN"]
PORT = int(os.environ.get("PORT", "8443"))
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
