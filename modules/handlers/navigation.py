# modules/handlers/navigation.py

import sqlite3
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    Application
)
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import (
    nav_buttons,
    admin_panel_kb
)
from modules.states import (
    STEP_MENU,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)
from .start import start_command
from .admin import show_admin_panel

# === Ініціалізація таблиці threads (за потреби для збереження base_msg_id) ===
def _init_threads():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()

# === Основна логіка меню (роутер для всіх callback_query, group=1) ===
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

    # ─── Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # ─── Адмін: пошук користувача ───
    if data == CB.ADMIN_SEARCH.value:
        # Вхід у ConversationHandler для пошуку
        return STEP_ADMIN_SEARCH

    # ─── Адмін: розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        # Вхід у ConversationHandler для розсилки
        return STEP_ADMIN_BROADCAST

    # ─── Якщо нічого не збіглося ─── повертаємо користувача до головного меню
    return await start_command(update, context)

# === Реєструємо загальний роутер у групі 1 ===
def register_navigation_handlers(app: Application):
    _init_threads()

    # Обробка кнопок “home” та “back”
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.HOME.value}$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.BACK.value}$"),
        group=1
    )

    # Основний menu_handler ловить усі інші callback_query
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
