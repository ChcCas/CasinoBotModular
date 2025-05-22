import asyncio
from flask import request, abort
from telegram import Update
from modules.config import WEBHOOK_URL

def register_routes(app, application):
    @app.route("/webhook", methods=["POST"])
    def webhook():
        if request.headers.get("content-type") == "application/json":
            data = request.get_json(force=True)
            update = Update.de_json(data, application.bot)
            asyncio.get_event_loop().create_task(application.process_update(update))
            return "ok"
        else:
            abort(403)

    @app.route("/set-webhook", methods=["GET"])
    def set_webhook():
        asyncio.run(application.bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        ))
        return "✅ Webhook встановлено!"

    @app.route("/")
    def index():
        return "Bot is alive!"
