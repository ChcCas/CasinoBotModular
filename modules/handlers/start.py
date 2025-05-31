# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.config import ADMIN_ID
from modules.keyboards import main_menu

# знаходимо корінь проєкту, щоб мати шлях до assets/welcome.gif
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Якщо адміністратор → кнопка “Адмін-панель”. Інакше – клавіатура client_menu(False).
    Відправляє welcome.gif або текст.
    """
    # Якщо це callback_query (натискання «Головне меню» або «Назад»), відповідаємо на нього:
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Якщо адмін – надсилаємо тільки «Адмін-панель»
    if user_id == ADMIN_ID:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🛠 Адмін-панель",
            reply_markup=main_menu(is_admin=True)
        )
        return

    # Усі інші користувачі – звичайне вітання та меню
    caption = "🎲 Ласкаво просимо до BIG GAME MONEY!"
    keyboard = main_menu(is_admin=False)

    if GIF_PATH.is_file():
        with GIF_PATH.open("rb") as gif_file:
            await context.bot.send_animation(
                chat_id=chat_id,
                animation=gif_file,
                caption=caption,
                reply_markup=keyboard
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=keyboard
        )

def register_start_handler(app: Application) -> None:
    """
    Реєструє команду /start у групі 0.
    """
    app.add_handler(CommandHandler("start", start_command), group=0)
