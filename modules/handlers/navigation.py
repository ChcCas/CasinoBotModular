import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    Application,
)
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import (
    PROVIDERS,
    PAYMENTS,
    nav_buttons,
    provider_buttons,
    payment_buttons,
    admin_panel_kb,
)
from modules.states import (
    STEP_MENU,
    STEP_DEPOSIT_AMOUNT,
    STEP_WITHDRAW_AMOUNT,
    STEP_REG_NAME,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST,
)
from .start import start_command
from .admin import show_admin_panel
from .profile import start_profile

# Якщо потрібно вести таблицю threads (зараз проєкт обходиться без неї,
# але залишаю заготівку на майбутнє):
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
    Основна логіка роутингу для всіх callback_query, що не потрапили у ConversationHandler-и.
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── Повернення «додому» або «назад» ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── «Мій профіль» (якщо користувач клікнув тут, але не в ConversationHandler) ───
    if data == CB.CLIENT_PROFILE.value:
        return await start_profile(update, context)

    # ─── Поповнення ───
    if data == CB.DEPOSIT_START.value:
        await query.message.reply_text("💸 Введіть суму для поповнення:", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    # ─── Виведення коштів ───
    if data == CB.WITHDRAW_START.value:
        await query.message.reply_text("💳 Введіть суму для виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    # ─── Реєстрація ───
    if data == "register":
        await query.message.reply_text("📝 Введіть ваше ім’я:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # ─── Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text("ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат", reply_markup=nav_buttons())
        return STEP_MENU

    # ─── Адмін: пошук користувача ───
    if data == CB.ADMIN_SEARCH.value:
        await query.message.reply_text("🔍 Введіть ID або картку для пошуку:", reply_markup=nav_buttons())
        return STEP_ADMIN_BROADCAST

    # ─── Адмін: розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        await query.message.reply_text("📢 Введіть текст для розсилки:", reply_markup=nav_buttons())
        return STEP_MENU

    # ─── Якщо нічого не збіглося — повернутися в меню
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    """
    Реєструє загальний CallbackQueryHandler для всіх невпійманих кнопок (група=1).
    """
    _init_threads()

    # Реєструємо «Головне меню» / «Назад»
    app.add_handler(CallbackQueryHandler(start_command, pattern="^home$"), group=1)
    app.add_handler(CallbackQueryHandler(start_command, pattern="^back$"), group=1)

    # Основний роутер для всіх інших callback_data → menu_handler
    app.add_handler(CallbackQueryHandler(menu_handler, pattern=".*"), group=1)
