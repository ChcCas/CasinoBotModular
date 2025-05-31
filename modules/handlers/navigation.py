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

    # 1) Якщо це «client_profile» або «client_find» → даємо можливість profile_conv спрацювати
    if data in (CB.CLIENT_PROFILE.value, CB.CLIENT_FIND.value):
        return None

    # 2) Якщо це «deposit_start» або «withdraw_start» → даємо можливість відповідному ConvHandler спрацювати
    if data in (CB.DEPOSIT_START.value, CB.WITHDRAW_START.value):
        return None

    # 3) Адмін-панель
    if data == CB.ADMIN_PANEL.value:
        return await show_admin_panel(update, context)

    # 4) «Назад» / «Головне меню»
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # 5) Реєстрація
    if data == CB.REGISTER.value:
        return None  # нехай Registration ConvHandler спрацює

    # 6) Допомога
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n"
            "/start — перезапуск\n"
            "📲 Питання — через чат з адміном",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # 7) Адмін: Пошук користувача
    if data == CB.ADMIN_SEARCH.value:
        return STEP_ADMIN_SEARCH

    # 8) Адмін: Розсилка
    if data == CB.ADMIN_BROADCAST.value:
        return STEP_ADMIN_BROADCAST

    # 9) Якщо нічого не збіглося — повернути в /start
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    _init_threads()

    # Спершу ловимо “home” / “back” (щоб повернутися до /start)
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.HOME.value}$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern=f"^{CB.BACK.value}$"),
        group=1
    )

    # Далі — усі інші CallbackQuery → menu_handler
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
