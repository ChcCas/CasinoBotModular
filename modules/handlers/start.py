# modules/handlers/start.py

from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

from modules.config import ADMIN_ID              # Ваш константний ID адміна
from modules.keyboards import main_menu, admin_panel_kb  # Імпортуємо дві різні клавіатури

# Шлях до assets/welcome.gif (якщо хочете залишити GIF)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Якщо це адміністратор — показуємо тільки адмін-панель
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "🛠 Адмін-панель",
            reply_markup=admin_panel_kb()
        )
        return

    # Інакше — стандартне вітання для клієнта
    caption = "🎲 Ласкаво просимо до CasinoBot!"
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
    Реєструє /start у диспетчері.
    """
    app.add_handler(CommandHandler("start", start_command))
