# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.keyboards import main_menu  # <-- імпорт із модуля modules.keyboards

# Визначаємо корінь проєкту (start.py → handlers → modules → src)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start: якщо є assets/welcome.gif — шлє GIF, інакше — просто текст.
    """
    caption  = "🎲 Ласкаво просимо до CasinoBot!"
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

def register_start_handler(app: Application) -> None:
    """
    Регіструємо /start у диспетчері.
    """
    app.add_handler(CommandHandler("start", start_command))
