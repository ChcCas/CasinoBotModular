# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.config import ADMIN_ID
from modules.keyboards import main_menu, admin_panel_kb
from modules.states import STEP_MENU

# Знаходимо корінь проєкту та шлях до GIF (за потреби)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробка /start або натискання кнопки “🏠 Головне меню”/“◀️ Назад”.
    Намагаємося відредагувати єдине повідомлення з головним меню, 
    а якщо не вдається — надсилаємо нове.
    """
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Вибираємо текст і клавіатуру залежно від того, чи адміністратор
    if user_id == ADMIN_ID:
        text = "🛠 Адмін-панель"
        keyboard = admin_panel_kb()
    else:
        text = "🎲 Ласкаво просимо до BIG GAME MONEY!"
        keyboard = main_menu(is_admin=False)

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        # Якщо в user_data вже є base_msg_id — пробуємо редагувати
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            msg = str(e).lower()
            # Ігноруємо, якщо повідомлення вже видалено або текст не змінився
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
                sent = await update.effective_chat.send_message(
                    text=text,
                    reply_markup=keyboard
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                # Якщо це інша помилка — кидаємо далі
                raise
    else:
        # Якщо base_msg_id ще немає — надсилаємо нове повідомлення
        sent = await update.effective_chat.send_message(
            text=text,
            reply_markup=keyboard
        )
        context.user_data["base_msg_id"] = sent.message_id

    return STEP_MENU

def register_start_handler(app: Application) -> None:
    """
    Регіструє CommandHandler("/start") у групі 0.
    """
    app.add_handler(CommandHandler("start", start_command), group=0)
