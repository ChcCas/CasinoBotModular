import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
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
from .admin import show_admin_panel, admin_search, admin_broadcast

# Якщо у вас немає окремого модуля registration.py, видаліть цей рядок:
# from .registration import register_name, register_phone, register_code

# === Якщо потрібна таблиця threads ===
def _init_threads():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

     # ─── Назад / Головне меню ─── 
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── Поповнення ───
    if data == CB.DEPOSIT_START.value:
        # імпортуємо start_deposit із deposit.py, якщо треба
        from .deposit import start_deposit
        return await start_deposit(update, context)

    # ─── Виведення ───
    if data == CB.WITHDRAW_START.value:
        from .withdraw import start_withdraw
        return await start_withdraw(update, context)

    # ─── Реєстрація (якщо у вас є registration.py) ───
    # if data == "register":
    #     return await register_name(update, context)

    # ─── Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # ─── Адмінський пошук ───
    if data == CB.ADMIN_SEARCH.value:
        return await admin_search(update, context)

    # ─── Адмінська розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        return await admin_broadcast(update, context)

    # ─── Якщо жодний із пунктів вище не спрацював ───
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    _init_threads()

    # Обробляємо кнопки “home” / “back” окремо (вони одразу кидають на start_command)
    app.add_handler(CallbackQueryHandler(start_command, pattern="^home$"), group=1)
    app.add_handler(CallbackQueryHandler(start_command, pattern="^back$"), group=1)

    # Далі обробляємо всі інші callback_query через menu_handler
    app.add_handler(CallbackQueryHandler(menu_handler, pattern=".*"), group=1)
