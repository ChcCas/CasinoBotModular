# modules/handlers/navigation.py

import sqlite3
import re
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import nav_buttons
from modules.states import (
    STEP_MENU,
    STEP_DEPOSIT_AMOUNT,
    STEP_WITHDRAW_AMOUNT,
    STEP_REG_NAME,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)
from .start import start_command
from .admin import show_admin_panel

def _init_threads():
    """
    Створює таблицю threads, якщо потрібна (в цьому прикладі не використовується безпосередньо).
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Загальний роутер для всіх CallbackQuery, які не обробили ConversationHandler-и з групи 0.
    Якщо callback_data відповідає початку Conversation (вони ловляться раніше), 
    то ми тут не робимо нічого (просто повертаємося). В іншому випадку — показуємо головне меню або
    обробляємо інші “одиночні” кнопки, наприклад, “Help”.
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    # 1) Адмін натиснув “🛠 Адмін-панель” → викликаємо show_admin_panel
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # 2) Якщо це початок одного зі сценаріїв, які вже мають свій ConversationHandler (група 0),
    #    просто повертаємося — ConversationHandler сам виконає свій початковий callback.
    if data in (
        CB.CLIENT_PROFILE.value,   # "client_profile"
        CB.DEPOSIT_START.value,   # "deposit_start"
        CB.WITHDRAW_START.value,  # "withdraw_start"
        CB.ADMIN_SEARCH.value,    # "admin_search"
        CB.ADMIN_BROADCAST.value  # "admin_broadcast"
    ):
        return

    # 3) Якщо це “Назад” чи “Головне меню” — викликаємо start_command
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # 4) Приклад обробки “Help”:
    if data == CB.HELP.value:
        base_id = context.user_data.get("base_msg_id")
        help_text = "ℹ️ Допомога:\n/start — перезапуск\n📲 Зверніться до підтримки, якщо є питання."
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=help_text,
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    raise
        else:
            sent = await update.callback_query.message.reply_text(
                help_text,
                reply_markup=nav_buttons()
            )
            context.user_data["base_msg_id"] = sent.message_id
        return STEP_MENU

    # 5) Якщо жоден з попередніх випадків не підходить — повертаємося до головного меню
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    """
    1) Перше — ініціалізуємо таблицю threads (якщо вам колись стане в пригоді).
    2) Реєструємо дві “пріоритетні” кнопки: “home” і “back” (група 1).
    3) Далі реєструємо menu_handler (група 1), який «ловитиме» всі інші callback_query.
    ConversationHandler-и (група 0) вже зареєстровані раніше і оброблять ті callback_data, що їм належать.
    """
    _init_threads()

    # «Головне меню» та «Назад» мають спрацьовувати миттєво та викликати start_command
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"),
        group=1
    )

    # Усі інші CallbackQuery, що не були оброблені у групі 0, потраплять сюди
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
