import os
from flask import Flask
from telegram.ext import ApplicationBuilder
from modules.config import TOKEN
from modules.routes import register_routes
from modules.handlers import setup_handlers

# === Flask app ===
app = Flask(__name__)

# === Telegram app ===
application = (
    ApplicationBuilder()
    .token(TOKEN)
    .concurrent_updates(True)
    .build()
)

# Підключення обробників
setup_handlers(application)

# Реєстрація Flask-маршрутів
register_routes(app, application)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
