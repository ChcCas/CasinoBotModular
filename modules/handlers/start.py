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
    Якщо є GIF, надсилаємо його з підписом, інакше – звичайне текстове повідомлення.
    В одному чаті зберігаємо тільки одне повідомлення (base_msg_id) і намагаємося його редагувати.
    """
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Визначаємо текст і клавіатуру залежно від ролі
    if user_id == ADMIN_ID:
        text = "🛠 Адмін-панель"
        keyboard = admin_panel_kb()
    else:
        text = "🎲 Ласкаво просимо до BIG GAME MONEY!"
        keyboard = main_menu(is_admin=False)

    base_id = context.user_data.get("base_msg_id")
    base_is_animation = context.user_data.get("base_is_animation", False)

    # Якщо є вже збережене повідомлення – пробуємо його редагувати
    if base_id:
        try:
            if base_is_animation and GIF_PATH.is_file():
                # Редагуємо анімацію неможливо, тому просто надсилаємо нове текстове
                sent = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard
                )
                context.user_data["base_msg_id"] = sent.message_id
                context.user_data["base_is_animation"] = False
            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
        except BadRequest as e:
            msg = str(e)
            if ("Message to edit not found" in msg) or ("Message is not modified" in msg):
                # Якщо не вдалося редагувати (наприклад, видалили) – надсилаємо нове
                if GIF_PATH.is_file() and user_id != ADMIN_ID:
                    # Для звичайних користувачів спочатку показуємо GIF, потім надсилаємо текст
                    with GIF_PATH.open("rb") as gif_file:
                        sent_anim = await context.bot.send_animation(
                            chat_id=chat_id,
                            animation=gif_file,
                            caption=text,
                            reply_markup=keyboard
                        )
                    context.user_data["base_msg_id"] = sent_anim.message_id
                    context.user_data["base_is_animation"] = True
                else:
                    sent_txt = await context.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=keyboard
                    )
                    context.user_data["base_msg_id"] = sent_txt.message_id
                    context.user_data["base_is_animation"] = False
            else:
                raise
    else:
        # Жодного вихідного повідомлення ще не було – надсилаємо
        if GIF_PATH.is_file() and user_id != ADMIN_ID:
            # Для звичайних користувачів показуємо GIF з підписом
            with GIF_PATH.open("rb") as gif_file:
                sent_anim = await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=gif_file,
                    caption=text,
                    reply_markup=keyboard
                )
            context.user_data["base_msg_id"] = sent_anim.message_id
            context.user_data["base_is_animation"] = True
        else:
            # Для адміністратора або якщо GIF відсутній: звичайний текст
            sent_txt = await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent_txt.message_id
            context.user_data["base_is_animation"] = False

    return STEP_MENU

def register_start_handler(app: Application) -> None:
    """
    Регіструє CommandHandler для /start.
   」
    """
    app.add_handler(CommandHandler("start", start_command), group=0)
