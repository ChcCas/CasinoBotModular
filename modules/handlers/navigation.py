# modules/handlers/navigation.py

import sqlite3
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
    Загальний роутер (група 1) для всіх callback_query, які не
    “підхоплені” у групі 0 (ConversationHandler’ами).
    1) Якщо callback_data відповідає початку Conversation (client_profile, deposit_start, withdraw_start, admin_search, admin_broadcast) — просто повертаємо None.
    2) Якщо “admin_panel” — викликаємо show_admin_panel.
    3) Якщо “home” або “back” — викликаємо start_command.
    4) Якщо “help” — редагуємо або надсилаємо повідомлення з текстом допомоги.
    5) Інакше — повертаємо start_command.
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    # 1) Адмін натиснув “🛠 Адмін-панель”
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # 2) Якщо це початок ConversationHandler (група 0) — ігноруємо тут
    if data in (
        CB.CLIENT_PROFILE.value,   # client_profile
        CB.DEPOSIT_START.value,    # deposit_start
        CB.WITHDRAW_START.value,   # withdraw_start
        CB.ADMIN_SEARCH.value,     # admin_search
        CB.ADMIN_BROADCAST.value   # admin_broadcast
    ):
        return

    # 3) Якщо “Назад” чи “Головне меню”
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # 4) “Допомога”
    if data == CB.HELP.value:
        text = "ℹ️ Допомога:\n/start — перезапустити бота\n📲 Зверніться до підтримки, якщо є питання."
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=text,
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.callback_query.message.reply_text(
                        text,
                        reply_markup=nav_buttons()
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.callback_query.message.reply_text(
                text,
                reply_markup=nav_buttons()
            )
            context.user_data["base_msg_id"] = sent.message_id
        return STEP_MENU

    # 5) В усіх інших випадках повертаємося до головного меню
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    """
    Регіструємо загальний навігаційний роутер (група 1):
      1) CallbackQueryHandler(start_command, pattern="^home$")
      2) CallbackQueryHandler(start_command, pattern="^back$")
      3) CallbackQueryHandler(menu_handler, pattern=".*")
    Усі ConversationHandler-и (група 0) мають бути додані раніше.
    """
    _init_threads()

    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
