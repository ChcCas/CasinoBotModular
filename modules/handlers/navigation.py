# modules/handlers/navigation.py

import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    Application
)
from modules.config import ADMIN_ID, DB_NAME
from modules.callbacks import CB
from modules.keyboards import (
    PROVIDERS,
    PAYMENTS,
    nav_buttons,
    provider_buttons,
    payment_buttons,
    admin_panel_kb
)
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

# === Ініціалізація таблиці threads ===
def _init_threads():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()

# === Основна логіка меню (Router для всіх callback_query) ===
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── Повернення «додому» або «назад» ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── Поповнення ───
    if data == "deposit":
        await query.message.reply_text(
            "💸 Введіть суму для поповнення:", reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    # ─── Виведення коштів ───
    if data in ("withdraw", CB.WITHDRAW_START.value):
        await query.message.reply_text(
            "💳 Введіть суму для виведення:", reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    # ─── Реєстрація ───
    if data == "register":
        await query.message.reply_text(
            "📝 Введіть ваше ім’я:", reply_markup=nav_buttons()
        )
        return STEP_REG_NAME

    # ─── Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # ─── Адмін: пошук користувача ───
    if data == "admin_search":
        return STEP_ADMIN_SEARCH

    # ─── Адмін: розсилка ───
    if data == "admin_broadcast":
        return STEP_ADMIN_BROADCAST

    # ─── Якщо нічого не збіглось ───
    return await start_command(update, context)

# === Реєструємо загальний роутер у групі 1 ===
def register_navigation_handlers(app: Application):
    _init_threads()

    # Команда /start та натискання кнопок “home”/“back” викликає start_command
    app.add_handler(
        CommandHandler("start", start_command),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"),
        group=1
    )

    # Основний menu_handler ловить усі інші callback_query
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
