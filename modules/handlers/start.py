# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from keyboards import main_menu   # <-- імпортуємо з keyboards.py, а не з «клавиатуры»

# ─── Знаходимо корінь проєкту (…/src/modules/handlers/start.py → …/src)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник команди /start:
     – якщо є файл assets/welcome.gif, надсилає його як анімацію;
     – інакше просто вітає текстом і клавіатурою.
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
    Додаємо /start до диспетчера.
    """
    application.add_handler(CommandHandler("start", start_command))
