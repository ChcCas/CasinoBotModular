# modules/handlers/navigation.py

import sqlite3
import re
from telegram import Update
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

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── Повернення “Головне меню” чи “Назад” ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # Решту сценаріїв (“deposit_start”, “withdraw_start” тощо) ловлять відповідні ConversationHandler-и.
    # Якщо нічого не спрацювало, повертаємося до головного меню:
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    _init_threads()
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"), group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"), group=1
    )
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"), group=1
    )
