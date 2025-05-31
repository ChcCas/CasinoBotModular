# modules/handlers/start.py

from pathlib import Path
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from modules.config import ADMIN_ID
from modules.keyboards import main_menu, admin_panel_kb
from modules.states import STEP_MENU

# Знаходимо корінь проєкту та шлях до GIF (якщо ви хочете надсилати анімований gif)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR   = PROJECT_ROOT / "assets"
GIF_PATH     = ASSETS_DIR / "welcome.gif"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробка команди /start або натискання кнопки “Головне меню” чи “Назад”.
    Відправляємо або редагуємо одне повідомлення з головним меню.
    """
    # Якщо це callback_query (натискання будь-якої кнопки з callback_data),
    # потрібно відповісти answer() перед редагуванням чи відправкою
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Підготуємо текст і клавіатуру залежно від того, чи це адмін
    if user_id == ADMIN_ID:
        text     = "🛠 Адмін-панель"
        keyboard = admin_panel_kb()
    else:
        text     = "🎲 Ласкаво просимо до BIG GAME MONEY!"
        keyboard = main_menu(is_admin=False)

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        # Якщо базове повідомлення вже є — редагуємо його
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=base_id,
            text=text,
            reply_markup=keyboard
        )
    else:
        # Якщо базового повідомлення ще нема — надсилаємо нове
        sent = await update.effective_chat.send_message(
            text=text,
            reply_markup=keyboard
        )
        context.user_data["base_msg_id"] = sent.message_id

    return STEP_MENU

def register_start_handler(app: Application) -> None:
    """
    Регіструємо CommandHandler("/start", start_command).
    """
    app.add_handler(CommandHandler("start", start_command), group=0)
