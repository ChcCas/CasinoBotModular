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
from modules.keyboards import nav_buttons
from modules.states import (
    STEP_MENU,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)
from .start import start_command
from .admin import show_admin_panel

# === 1) Ініціалізація таблиці threads (за потреби) ===
def _init_threads():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()

# === 2) Основна логіка меню (роутер для всіх callback_query) ===
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── 2.1 Якщо це саме “client_profile” або “client_find” —
    #      повертаємо None, щоб ConversationHandler профілю спрацював раніше (group=0).
    if data in (CB.CLIENT_PROFILE.value, CB.CLIENT_FIND.value):
        return None

    # ─── 2.2 Якщо це “deposit_start” або “withdraw_start” —
    #      повертаємо None, щоб відповідний ConversationHandler (депозит/виведення) спрацював.
    if data in (CB.DEPOSIT_START.value, CB.WITHDRAW_START.value):
        return None

    # ─── 2.3 Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── 2.4 Повернення «додому» або «назад» ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── 2.5 Реєстрація (якщо є окремий сценарій) ───
    if data == CB.REGISTER.value:
        # Якщо у вас є окремий ConversationHandler для “register”, він спрацює.
        return None

    # ─── 2.6 Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n"
            "/start — перезапуск\n"
            "📲 Питання — через чат з адміном",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # ─── 2.7 Адмін: пошук користувача ───
    if data == CB.ADMIN_SEARCH.value:
        # Входимо у відповідний ConversationHandler, який ловить STEP_ADMIN_SEARCH
        return STEP_ADMIN_SEARCH

    # ─── 2.8 Адмін: розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        # Входимо у відповідний ConversationHandler, який ловить STEP_ADMIN_BROADCAST
        return STEP_ADMIN_BROADCAST

    # ─── 2.9 Якщо жоден з вище перелічених — повертаємо користувача до /start ───
    return await start_command(update, context)

# === 3) Реєструємо загальний роутер у групі 1 ===
def register_navigation_handlers(app: Application):
    _init_threads()

    # 3.1 Обробляємо кнопки “home” та “back” окремо (щоб точно повернутися в /start)
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.HOME.value}$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.BACK.value}$"),
        group=1
    )

    # 3.2 Основний menu_handler ловить усі інші callback_query
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
