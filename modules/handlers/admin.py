# modules/handlers/navigation.py

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
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME
from keyboards import PROVIDERS, PAYMENTS, nav_buttons, provider_buttons, payment_buttons
from states import (
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
return await show_admin_panel(query)
from modules.db import search_user, broadcast_message

# Ініціалізація таблиці threads
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
            CallbackQueryHandler(start_command, pattern="^(home|back)$", per_message=True),
        ],
        states={
            STEP_MENU: [
                CallbackQueryHandler(menu_handler, pattern=".*", per_message=True)
            ],
            # — Реєстрація —
            STEP_REG_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            STEP_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            STEP_REG_CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_code)],
            # — Профіль (введення картки) —
            STEP_CLIENT_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
            STEP_PROVIDER: [
                CallbackQueryHandler(
                    process_provider,
                    pattern="^(" + "|".join(map(re.escape, PROVIDERS)) + ")$",
                    per_message=True,
                )
            ],
            STEP_PAYMENT: [
                CallbackQueryHandler(
                    process_payment,
                    pattern="^(" + "|".join(map(re.escape, PAYMENTS)) + ")$",
                    per_message=True,
                )
            ],
            # — Поповнення —
            STEP_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_CONFIRM_FILE:   [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, process_file)],
            STEP_CONFIRMATION:   [CallbackQueryHandler(confirm_submission, pattern="^confirm$", per_message=True)],
            # — Виведення —
            STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(
                                      process_withdraw_method,
                                      pattern="^(" + "|".join(map(re.escape, PAYMENTS)) + ")$",
                                      per_message=True
                                   )],
            STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
            STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$", per_message=True)],
            # — Адмін —
            STEP_ADMIN_SEARCH:    [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search)],
            STEP_ADMIN_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast)],
        },
        fallbacks=[
            CallbackQueryHandler(start_command, pattern="^(home|back)$", per_message=True),
        ],
        per_message=True,
        per_chat=True,
        name="casino_conversation",
    )

    app.add_handler(conv, group=1)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # — Адмін-панель —
    if data == "admin_panel":
        return await show_admin_panel(query)

    # — Головне меню / назад —
    if data in ("home", "back"):
        return await start_command(update, context)

    # — Профіль клієнта —
    if data == "client_profile":
        from .profile import start_profile
        return await start_profile(update, context)

    if data == "client_find_card":
        from .profile import find_card
        return await find_card(update, context)

    # — Поповнення —
    if data == "deposit":
        await query.message.reply_text("💸 Введіть суму для поповнення:", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    # — Виведення —
    if data in ("withdraw", "WITHDRAW_START"):
        await query.message.reply_text("💳 Введіть суму для виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    # — Реєстрація —
    if data == "register":
        await query.message.reply_text("📝 Введіть ваше ім’я:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # — Допомога —
    if data == "help":
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск бота\nКонтакт підтримки: @admin",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    return STEP_MENU


# Реєстрація нового користувача
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["reg_name"] = name
    await update.message.reply_text("📞 Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.match(r"^0\\d{9}$", phone):
        await update.message.reply_text("❗️ Невірний формат. Спробуйте ще раз:", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    context.user_data["reg_phone"] = phone
    await update.message.reply_text("🔑 Введіть 4-значний код підтвердження:", reply_markup=nav_buttons())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    # Перевіряємо, що код — це рівно 4 цифри
    if not re.match(r"^\d{4}$", code):
        await update.message.reply_text(
            "❗️ Код має складатися з 4 цифр. Спробуйте ще раз:",
            reply_markup=nav_buttons()
        )
        return STEP_REG_CODE

    # Далі ваша логіка: збереження коду, вставка в БД тощо
    user_id = update.effective_user.id
    name = context.user_data.get("reg_name")
    phone = context.user_data.get("reg_phone")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO registrations (user_id, name, phone) VALUES (?, ?, ?)",
            (user_id, name, phone)
        )
        conn.commit()

    await update.message.reply_text(
        "✅ Реєстрація успішна! Оберііть дію:",
        reply_markup=nav_buttons()
    )
    return STEP_MENU