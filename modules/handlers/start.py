# modules/handlers/start.py

import os
from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

from keyboards import main_menu

# ─── Визначаємо корінь проєкту так, щоб шукати assets/ на рівні репозиторію
#
# Структура:
# /opt/render/project/
# ├─ assets/
# │   └─ welcome.gif
# └─ src/
#     └─ modules/
#         └─ handlers/
#             └─ start.py
#
# Тобто: start.py → handlers → modules → src → project
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /start.
    Якщо у папці assets є welcome.gif — надсилає його як анімацію.
    Інакше — просто текстове привітання.
    """
    caption = "🎲 Ласкаво просимо до CasinoBot!"
    kb      = main_menu()

    if GIF_PATH.is_file():
        # Надсилаємо GIF-анімацію, якщо файл знайдено
        with GIF_PATH.open("rb") as gif:
            await update.message.reply_animation(
                gif,
                caption=caption,
                reply_markup=kb
            )
    else:
        # Файл відсутній — надсилаємо просте текстове повідомлення
        await update.message.reply_text(
            caption,
            reply_markup=kb
        )


def register_start_handler(application: Application) -> None:
    """
    Реєструє хендлер для /start у головному Application.
    """
    application.add_handler(CommandHandler("start", start_command))
