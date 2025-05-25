# modules/config.py
import os

# Telegram token
TOKEN    = os.environ["TOKEN"]
# Ваш Telegram-ID адміністратора
ADMIN_ID = int(os.environ["ADMIN_ID"])
# Ім’я файлу бази даних SQLite
DB_NAME  = os.environ.get("DB_NAME", "bot.db")