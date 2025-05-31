# modules/config.py

import os
from dotenv import load_dotenv

# ─── Завантажуємо змінні середовища з .env ────────────────────────────────────
load_dotenv()

# ─── Токен бота (отриманий у BotFather) ────────────────────────────────────
TOKEN = os.getenv("TOKEN")

# ─── Публічний webhook URL (як у BotFather) ─────────────────────────────────
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# ─── ID адміністратора (ваш власний Telegram user_id) ────────────────────────
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ─── Порт для webhook: зазвичай Render чи Heroku надають свій PORT ───────────
PORT = int(os.getenv("PORT", "8443"))

# ─── Назва файлу SQLite для бази даних ──────────────────────────────────────
DB_NAME = os.getenv("DB_NAME", "bot.db")

# ─── Глобальний об’єкт BOT_INSTANCE ─────────────────────────────────────────
# Спочатку None, а після створення Application (app = ApplicationBuilder().build())
# у main.py ми присвоїмо сюди actual bot: BOT_INSTANCE = app.bot
BOT_INSTANCE = None
