# modules/handlers/withdraw.py

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
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
from modules.keyboards import nav_buttons, payment_buttons, PAYMENTS
from modules.states import (
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM
)

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Користувач натиснув “💸 Вивести кошти” (callback_data="withdraw_start").
    Просимо ввести суму для виведення.
    """
    await update.callback_query.answer()
    text = "💳 Введіть суму для виведення:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_AMOUNT

async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Користувач увів суму виведення.
    Якщо помилка конвертації — просимо повторити.
    Інакше — зберігаємо суму і переходимо до вибору методу.
    """
    text_in = update.message.text.strip()
    try:
        amount = float(text_in)
    except ValueError:
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text="❗️ Невірний формат суми. Введіть число (наприклад, 100):",
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                # Якщо нічого фактично не змінилося або повідомлення видалене — надсилаємо нове
                msg = str(e)
                if "Message is not modified" not in msg and "Message to edit not found" not in msg:
                    raise
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="💳 Оберіть метод виведення:",
                reply_markup=payment_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message is not modified" not in msg and "Message to edit not found" not in msg:
                raise
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Користувач обрав метод виведення (callback_data ∈ PAYMENTS).
    Зберігаємо його і просимо ввести деталі (номер картки або гаманець).
    """
    await update.callback_query.answer()
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="💳 Введіть реквізити (номер картки або гаманець):",
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message is not modified" not in msg and "Message to edit not found" not in msg:
                raise
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Користувач ввів свої реквізити (текст).
    Зберігаємо їх і показуємо кнопку «Підтвердити».
    """
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити", callback_data=CB.WITHDRAW_CONFIRM.value)
    ]])
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="✅ Натисніть «Підтвердити», щоб завершити:",
                reply_markup=kb
            )
        except BadRequest as e:
            msg = str(e)
            if "Message is not modified" not in msg and "Message to edit not found" not in msg:
                raise
    return STEP_WITHDRAW_CONFIRM

async def confirm_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Користувач натиснув «Підтвердити» (callback_data="withdraw_confirm").
    Зберігаємо запис у таблицю withdrawals і показуємо повідомлення про успішне
    створення замовлення на виведення.
    """
    await update.callback_query.answer()
    user = update.effective_user
    amount  = context.user_data.get("withdraw_amount")
    method  = context.user_data.get("withdraw_method")
    details = context.user_data.get("withdraw_details")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO withdrawals
              (user_id, username, amount, method, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user.id, user.username, amount, method, details)
        )
        conn.commit()

    base_id = context.user_data.get("base_msg_id")
    final_text = "💸 Ваше замовлення на виведення отримано. Очікуйте обробки."
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=final_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message is not modified" not in msg and "Message to edit not found" not in msg:
                raise

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

withdraw_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(withdraw_start, pattern=f"^{CB.WITHDRAW_START.value}$")
    ],
    states={
        STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
        STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(process_withdraw_method, pattern="^(" + "|".join(PAYMENTS) + ")$")],
        STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
        STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(confirm_withdraw, pattern=f"^{CB.WITHDRAW_CONFIRM.value}$")],
    },
    fallbacks=[
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_withdraw_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler для сценарію виведення (група 0).
    """
    app.add_handler(withdraw_conv, group=0)
