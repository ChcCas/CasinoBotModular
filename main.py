import os
from telegram.ext import Application
from modules.handlers import get_conv_handler  # ВАЖЛИВО! Імпортуємо get_conv_handler

# 1) Змінні оточення (Render автоматично задає PORT)
TOKEN       = os.environ["TOKEN"]
PORT        = int(os.environ.get("PORT", "8443"))
WEBHOOK_URL = os.environ["WEBHOOK_URL"]  # наприклад: https://casinobotmodular.onrender.com/webhook

def main():
    # 2) Створюємо екземпляр бота
    app = Application.builder().token(TOKEN).build()

    # 3) Підключаємо ConversationHandler із modules/handlers.py
    app.add_handler(get_conv_handler())  # Додаємо хендлер

    # 4) Запускаємо webhook-сервер + Telegram-клієнт в одному asyncio-циклі
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()