# modules/handlers/navigation.py

import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
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
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_DEPOSIT_AMOUNT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST,
)
from .start import start_command
from .admin import (
    show_admin_panel,
    admin_search,
    admin_broadcast,
    confirm_withdrawal_notification,  # має обробляти callback_type="admin_confirm_card:..."
)
from .deposit import deposit_conv
from .withdraw import withdraw_conv
from .profile import profile_conv
from .registration import registration_conv  # окремий ConversationHandler для реєстрації

# === Ініціалізація таблиці threads (якщо потрібно) ===
def _init_threads():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()


# === Основна логіка меню (загальний роутер) ===
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # --------- Адмін-панель ---------
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # --------- Повернення додому або назад ---------
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # --------- Поповнення ---------
    if data == "deposit":
        await query.message.reply_text(
            "💸 Введіть суму для поповнення:", reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    # --------- Виведення коштів ---------
    if data in ("withdraw", CB.WITHDRAW_START.value):
        await query.message.reply_text(
            "💳 Введіть суму для виведення:", reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    # --------- Реєстрація ---------
    if data == "register":
        await query.message.reply_text(
            "📝 Введіть ваше ім’я:", reply_markup=nav_buttons()
        )
        return STEP_REG_NAME

    # --------- Допомога ---------
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # --------- Адмін: пошук користувача (текстовий ввід) ---------
    if data == "admin_search":
        # переходимо у відповідний ConversationHandler (STEP_ADMIN_SEARCH)
        return STEP_ADMIN_SEARCH

    # --------- Адмін: розсилка (текстовий ввід) ---------
    if data == "admin_broadcast":
        return STEP_ADMIN_BROADCAST

    # --------- Якщо не впізнали callback, повертаємо в меню ---------
    return await start_command(update, context)


# === Реєстрація всіх хендлерів навігації ===
def register_navigation_handlers(app: Application):
    # 1) Ініціалізація таблиці threads (якщо використовується)
    _init_threads()

    # 2) ConversationHandler’и для великих сценаріїв (група=0)
    #    ───────────── profile_conv ─────────────
    #    ловить “client_profile” та обробляє введення картки
    app.add_handler(profile_conv, group=0)

    #    ───────────── deposit_conv ─────────────
    #    весь сценарій депозиту (STEP_CLIENT_CARD, STEP_PROVIDER, STEP_PAYMENT, STEP_DEPOSIT_AMOUNT, STEP_CONFIRM_FILE, STEP_CONFIRMATION)
    app.add_handler(deposit_conv, group=0)

    #    ───────────── withdraw_conv ─────────────
    #    весь сценарій виведення (STEP_WITHDRAW_AMOUNT, STEP_WITHDRAW_METHOD, STEP_WITHDRAW_DETAILS, STEP_WITHDRAW_CONFIRM)
    app.add_handler(withdraw_conv, group=0)

    #    ───────────── registration_conv ─────────────
    #    весь сценарій реєстрації (STEP_REG_NAME, STEP_REG_PHONE, STEP_REG_CODE)
    app.add_handler(registration_conv, group=0)

    #    ───────────── Адмін-підтвердження картки ─────────────
    #    коли адміністратор натискає “admin_confirm_card:<user_id>:<card>”
    app.add_handler(
        CallbackQueryHandler(confirm_withdrawal_notification,  # або вище називається confirm_card?
                             pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )

    #    ───────────── Адмін: пошук користувача текстом ─────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search),
        group=0
    )

    #    ───────────── Адмін: розсилка текстом ─────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )

    # 3) Загальний роутер для всіх інших callback_query (група=1)
    app.add_handler(
        CallbackQueryHandler(menu_router, pattern=".*"),
        group=1
    )
