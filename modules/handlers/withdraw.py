# modules/handlers/withdraw.py

import sqlite3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import nav_buttons, payment_buttons
from modules.states import (
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
    STEP_MENU
)

async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вхід у сценарій «Вивести кошти».
    Питаємо суму для виведення.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💳 Введіть суму для виведення:",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_AMOUNT

async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт ввів суму:
    1) Зберігаємо її в user_data
    2) Переходимо до вибору методу (Card / Crypto)
    """
    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть вірну числову суму:",
            reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount
    await update.message.reply_text(
        "💳 Оберіть метод виведення:", reply_markup=payment_buttons()
    )
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт обрав метод «Карта» або «Криптопереказ».
    Питаємо деталі (номер карти або гаманець).
    """
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method

    await update.callback_query.message.reply_text(
        f"💳 Введіть реквізити для {method} (наприклад, номер картки або адрес гаманця):",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт ввів реквізити.
    Просимо підтвердження виведення.
    """
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити виведення", callback_data="withdraw_confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])

    amt = context.user_data.get("withdraw_amount")
    method = context.user_data.get("withdraw_method")
    await update.message.reply_text(
        f"💳 Ви хочете вивести {amt} UAH через {method} ({details}).\n"
        "Натисніть «✅ Підтвердити виведення», щоб завершити.",
        reply_markup=kb
    )
    return STEP_WITHDRAW_CONFIRM

async def confirm_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт натиснув «✅ Підтвердити виведення» (callback_data="withdraw_confirm").
    Зберігаємо у таблицю withdrawals і повідомляємо користувача.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    amount = context.user_data.get("withdraw_amount")
    method = context.user_data.get("withdraw_method")
    details = context.user_data.get("withdraw_details")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO withdrawals (user_id, amount, method, details)
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, method, details))
    conn.commit()
    conn.close()

    text = f"💸 Ваше виведення {amount} UAH через {method} ({details}) створено. Очікуйте підтвердження."
    keyboard = nav_buttons()
    await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    return STEP_MENU

def register_withdraw_handlers(app: Application) -> None:
    """
    Регіструємо ConversationHandler(«Вивести») у групі 0.
    """
    withdraw_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_withdraw, pattern=f"^{CB.WITHDRAW_START.value}$")
        ],
        states={
            STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(process_withdraw_method,
                                                          pattern="^(" + "|".join(["Карта", "Криптопереказ"]) + ")$")],
            STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
            STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(confirm_withdraw, pattern="^withdraw_confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True
    )

    app.add_handler(withdraw_conv, group=0)
