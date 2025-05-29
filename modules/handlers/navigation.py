import os
import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,        # ← вот он
)

from modules.config import ADMIN_ID, DB_NAME
from modules.keyboards import PROVIDERS, PAYMENTS, nav_buttons, provider_buttons, payment_buttons
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
# … остальные импорты …

from .profile import start_profile, profile_enter_card, profile_enter_phone
from .registration import registration_start, register_name, register_phone, register_code
from .admin import show_admin_panel, admin_search, admin_broadcast

def _init_threads():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                user_id INTEGER PRIMARY KEY,
                base_msg_id INTEGER
            )
        """)
        conn.commit()

def register_navigation_handlers(app):
    _init_threads()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(start_command, pattern="^(home|back)$"),
        ],
        states={
            STEP_MENU: [CallbackQueryHandler(menu_handler, pattern=".*")],
            # … тут перераховані ваші стани, як у прикладі вище …
        },
        fallbacks=[CallbackQueryHandler(start_command, pattern="^(home|back)$")],
        per_message=True,
        per_chat=True,
        name="casino_conversation",
    )
    app.add_handler(conv, group=1)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_panel":
        return await show_admin_panel(update, context)

    if data in ("home", "back"):
        return await start_command(update, context)

    if data == "client_profile":
        return await start_profile(update, context)

    if data == "client_find_card":
        return await profile_enter_card(update, context)  # пошук картки

    if data == "deposit":
        await query.message.reply_text("💸 Введіть суму для поповнення:", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    if data in ("withdraw", "WITHDRAW_START"):
        await query.message.reply_text("💳 Введіть суму для виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    if data == "register":
        return await registration_start(update, context)

    if data == "help":
        await query.message.reply_text(
            "ℹ️ /start — перезапуск\nКонтакт підтримки: @admin",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    return STEP_MENU
