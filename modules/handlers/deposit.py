# modules/handlers/deposit.py

import re
import sqlite3
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
from modules.db import search_user  # для перевірки, чи існує картка у БД
from modules.callbacks import CB
from modules.keyboards import nav_buttons, provider_buttons, payment_buttons
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_CONFIRM,
    STEP_MENU
)

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вхід у сценарій «Поповнити» (клієнт натиснув «💰 Поповнити»).
    Питаємо у користувача суму.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💸 Введіть суму для поповнення:",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт ввів суму:
    1) Зберігаємо її у user_data
    2) Переходимо до вибору провайдера
    """
    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть правильну числову суму:",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    await update.message.reply_text(
        "🎰 Оберіть провайдера:", reply_markup=provider_buttons()
    )
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт обрав провайдера («СТАРА СИСТЕМА» або «НОВА СИСТЕМА»).
    """
    provider = update.callback_query.data  # “СТАРА СИСТЕМА” або “НОВА СИСТЕМА”
    context.user_data["deposit_provider"] = provider

    await update.callback_query.message.reply_text(
        "💳 Оберіть метод оплати:", reply_markup=payment_buttons()
    )
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт обрав метод (наприклад, «Карта» або «Криптопереказ»).
    Питаємо останній крок – підтвердження.
    """
    payment = update.callback_query.data
    context.user_data["deposit_payment"] = payment

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити поповнення", callback_data="deposit_confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])
    await update.callback_query.message.reply_text(
        f"💰 Ви хочете поповнити {context.user_data['deposit_amount']} UAH\n"
        f"Провайдер: {context.user_data['deposit_provider']}\n"
        f"Метод: {context.user_data['deposit_payment']}\n\n"
        "Натисніть «✅ Підтвердити поповнення», щоб завершити.",
        reply_markup=kb
    )
    return STEP_DEPOSIT_CONFIRM

async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли клієнт натиснув «✅ Підтвердити поповнення» (callback_data="deposit_confirm").
    Зберігаємо в БД і повідомляємо користувача.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    amount = context.user_data.get("deposit_amount")
    provider = context.user_data.get("deposit_provider")
    payment = context.user_data.get("deposit_payment")

    # Запис у таблицю deposits
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO deposits (user_id, amount, provider, payment_method)
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, provider, payment))
    conn.commit()
    conn.close()

    text = f"💸 Ваше поповнення {amount} UAH за {provider}/{payment} успішно створено.\nОчікуйте підтвердження."
    keyboard = nav_buttons()
    await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    return STEP_MENU

def register_deposit_handlers(app: Application) -> None:
    """
    Регіструємо ConversationHandler(«Поповнити») у групі 0.
    """
    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_deposit, pattern=f"^{CB.DEPOSIT_START.value}$")
        ],
        states={
            STEP_DEPOSIT_AMOUNT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_DEPOSIT_PROVIDER: [CallbackQueryHandler(process_deposit_provider,
                                                         pattern="^(" + "|".join(["СТАРА СИСТЕМА", "НОВА СИСТЕМА"]) + ")$")],
            STEP_DEPOSIT_PAYMENT:  [CallbackQueryHandler(process_deposit_payment,
                                                         pattern="^(" + "|".join(["Карта", "Криптопереказ"]) + ")$")],
            STEP_DEPOSIT_CONFIRM:  [CallbackQueryHandler(confirm_deposit, pattern="^deposit_confirm$")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True
    )

    app.add_handler(deposit_conv, group=0)
