# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.config import ADMIN_ID
from modules.keyboards import main_menu, admin_panel_kb
from modules.states import STEP_MENU

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробка /start або натискання кнопки “Головне меню”/“Назад”.
    Надсилається або редагується єдине повідомлення з головним меню.
    """
    # Якщо це callback_query — відповідаємо на неї (щоб зникло "Loading...").
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Вибираємо текст і клавіатуру залежно від того, чи адмін.
    if user_id == ADMIN_ID:
        text = "🛠 Адмін-панель"
        keyboard = admin_panel_kb()
    else:
        text = "🎲 Ласкаво просимо до BIG GAME MONEY!"
        keyboard = main_menu(is_admin=False)

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        # Спробуємо редагувати наявне повідомлення.
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            # Ігноруємо, якщо повідомлення не знайдено чи не змінилося.
            msg = str(e)
            if ("Message is not modified" not in msg
                    and "Message to edit not found" not in msg):
                raise
    else:
        # Надсилаємо нове повідомлення і запам'ятовуємо його ID.
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard
        )
        context.user_data["base_msg_id"] = sent.message_id

    return STEP_MENU

def register_start_handler(app: Application) -> None:
    """
    Регіструє CommandHandler для /start.
    Повинен бути в group=0, щоб спрацьовував перед загальною обробкою callback_query.
    """
    app.add_handler(CommandHandler("start", start_command), group=0)
