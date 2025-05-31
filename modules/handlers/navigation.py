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
    query = update.callback_query
    data = query.data
    await query.answer()

    # Адмін-панель
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # Якщо callback_data запускає ConversationHandler (група 0) — ігноруємо
    if data in (
        CB.CLIENT_PROFILE.value,
        CB.DEPOSIT_START.value,
        CB.WITHDRAW_START.value,
        CB.ADMIN_SEARCH.value,
        CB.ADMIN_BROADCAST.value
    ):
        return

    # Назад / Головне меню
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # Допомога
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

    # Якщо нічого не збіглося — повертаємося до /start
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    _init_threads()

    # CallbackQueryHandler для “home”
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"),
        group=1
    )
    # CallbackQueryHandler для “back”
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"),
        group=1
    )
    # Основний menu_handler
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
