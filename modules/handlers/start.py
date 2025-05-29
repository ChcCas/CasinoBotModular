# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.keyboards import main_menu  # переконайтесь, що цей файл називається keyboards.py

# знаходимо корінь проєкту: start.py → handlers → modules → src
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start:
    – якщо знайдено assets/welcome.gif, надсилаємо його як анімацію;
    – інакше просто вітаємо текстом.
    Для меню передаємо is_admin=False.
    """
    caption = "🎲 Ласкаво просимо до CasinoBot!"
    # Передаємо флаг is_admin=False (це звичайний користувач)
    keyboard = main_menu(is_admin=False)

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
    Регіструємо обробник /start у диспетчері.
    """
    app.add_handler(CommandHandler("start", start_command))
