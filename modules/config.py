# modules/config.py
import os
from dotenv import load_dotenv

# подгружаем .env из корня проекта
load_dotenv()

TOKEN       = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "0"))
PORT        = int(os.getenv("PORT", "8443"))
DB_NAME     = os.getenv("DB_NAME", "bot.db")
