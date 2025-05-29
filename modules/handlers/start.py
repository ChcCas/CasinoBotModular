# modules/handlers/start.py

# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from keyboards import main_menu  # тут імпортуємо з keyboards.py

# Визначаємо корінь проєкту: start.py → handlers → modules → src → project
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /start.
    Якщо є файл assets/welcome.gif — відправляє його як анімацію,
    інакше — просто текстове привітання з кнопками.
    """
    caption = "🎲 Ласкаво просимо до CasinoBot!"
    keyboard = main_menu()

    if GIF_PATH.is_file():
        with GIF_PATH.open("rb") as gif_file:
            await update.message.reply_animation(
                gif_file,
                caption=caption,
                reply_markup=keyboard
            )
    else:
        await update.message.reply_text(
            caption,
            reply_markup=keyboard
        )

def register_start_handler(application: Application) -> None:
    """
    Реєструє CommandHandler для /start у додатку.
    """
    application.add_handler(CommandHandler("start", start_command))
