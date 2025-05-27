# modules/handlers/deposit.py

import sqlite3
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

from modules.config import ADMIN_ID, DB_NAME
from keyboards import provider_buttons, payment_buttons, nav_buttons
from states import (
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_DEPOSIT_AMOUNT,
    STEP_MENU,
)

def register_deposit_handlers(app):
    # а) початок флоу: натискання “💰 Поповнити”
    app.add_handler(
        CallbackQueryHandler(deposit_start, pattern="^deposit$"),
        group=0
    )
    # б) вибір провайдера
    app.add_handler(
        CallbackQueryHandler(
            deposit_process_provider,
            pattern="^(" + "|".join(provider_buttons().to_dict()['inline_keyboard'][0][i]['callback_data']
                                 for i in range(len(provider_buttons().to_dict()['inline_keyboard'][0]))) + ")$"
        ),
        group=1
    )
    # в) вибір способу оплати
    app.add_handler(
        CallbackQueryHandler(deposit_process_payment, pattern="^(Карта|Криптопереказ)$"),
        group=2
    )
    # г) введення суми
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_process_amount),
        group=3
    )

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт флоу поповнення: показуємо список провайдерів."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Оберіть провайдера для поповнення:",
        reply_markup=provider_buttons()
    )
    return STEP_PROVIDER

async def deposit_process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Після вибору провайдера — просимо спосіб оплати."""
    provider = update.callback_query.data
    context.user_data["deposit_provider"] = provider
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        f"Ви обрали провайдера {provider}. Тепер оберіть спосіб оплати:",
        reply_markup=payment_buttons()
    )
    return STEP_PAYMENT

async def deposit_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Після вибору способу — просимо суму."""
    payment = update.callback_query.data
    context.user_data["deposit_payment"] = payment
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        f"Спосіб оплати: {payment}. Введіть суму поповнення (ціле число):",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

async def deposit_process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отримуємо суму, дістаємо картку з БД і відправляємо адміну заявку."""
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text(
            "Невірна сума — введіть будь ласка позитивне число.",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    amount = int(text)
    user_id = update.effective_user.id

    # дістаємо картку з бази
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.execute(
            "SELECT card FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cur.fetchone()

    if not row:
        # якщо користувач не авторизований
        await update.message.reply_text(
            "Ви ще не авторизувалися в профілі. Спочатку натисніть «Мій профіль».",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    card = row[0]
    provider = context.user_data.get("deposit_provider")
    payment = context.user_data.get("deposit_payment")

    # формуємо повідомлення адміну
    msg = (
        f"🆕 Заявка на поповнення від {update.effective_user.full_name} ({user_id}):\n"
        f"• Картка: {card}\n"
        f"• Провайдер: {provider}\n"
        f"• Оплата: {payment}\n"
        f"• Сума: {amount}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    await update.message.reply_text(
        "Ваша заявка успішно відправлена адміністратору 👍",
        reply_markup=nav_buttons()
    )
    return STEP_MENU
