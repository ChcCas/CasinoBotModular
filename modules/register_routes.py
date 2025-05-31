# register_routes.py

import asyncio
from flask import request, abort
from telegram import Update
from modules.config import WEBHOOK_URL

def register_routes(app, application):
    """
    Реєструє Flask-роути для Telegram Webhook.
    Ми ініціалізуємо `application` лише один раз (при старті),
    а далі в кожному запиті просто створюємо задачі в існуючому event loop.
    """

    # Отримуємо поточний event loop (створюється при запуску Flask)
    loop = asyncio.get_event_loop()

    # 1) Один раз ініціалізуємо Telegram-бот (Application)
    loop.run_until_complete(application.initialize())

    @app.route("/webhook", methods=["POST"])
    def webhook():
        # Перевіряємо, що контент — JSON
        if request.headers.get("content-type") == "application/json":
            data = request.get_json(force=True)
            update = Update.de_json(data, application.bot)

            # Додаємо в чергу обробки (не чекаємо завершення)
            loop.create_task(application.process_update(update))
            return "ok"
        else:
            abort(403)

    @app.route("/set-webhook", methods=["GET"])
    def set_webhook():
        # Викликаємо асинхронно set_webhook Telegram-API
        loop.create_task(
            application.bot.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True
            )
        )
        return "✅ Webhook встановлено!"

    @app.route("/")
    def index():
        return "Bot is alive!"
