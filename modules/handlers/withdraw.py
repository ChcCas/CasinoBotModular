# modules/handlers/withdraw.py

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
    Entry point: користувач натиснув “💸 Вивести кошти” (callback_data="withdraw_start").
    Надсилаємо одне базове повідомлення та зберігаємо message_id.
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
    Крок STEP_WITHDRAW_AMOUNT: користувач вводить суму. Перевіряємо, чи це число.
    Якщо ні — редагуємо повідомлення з помилкою. Якщо так — редагуємо з клавіатурою методу.
    """
    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="❗️ Невірний формат суми. Введіть число (наприклад, 100):",
                reply_markup=nav_buttons()
            )
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="Оберіть метод виведення:",
            reply_markup=payment_buttons()
        )
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_WITHDRAW_METHOD: користувач обрав “Карта” чи “Криптопереказ”.
    Зберігаємо і редагуємо повідомлення, запитуючи реквізити.
    """
    await update.callback_query.answer()
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="💳 Введіть реквізити (номер картки або гаманець):",
            reply_markup=nav_buttons()
        )
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_WITHDRAW_DETAILS: користувач ввів реквізити.
    Редагуємо повідомлення, додаючи кнопку “Підтвердити виведення”.
    """
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити виведення", callback_data=CB.WITHDRAW_CONFIRM.value)
    ]])
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="✅ Натисніть «Підтвердити виведення», щоб завершити.",
            reply_markup=kb
        )
    return STEP_WITHDRAW_CONFIRM

async def confirm_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_WITHDRAW_CONFIRM: користувач натиснув “✅ Підтвердити виведення”.
    Зберігаємо у таблицю withdrawals, редагуємо повідомлення та завершуємо сценарій.
    """
    await update.callback_query.answer()
    user = update.effective_user

    amount  = context.user_data.get("withdraw_amount")
    method  = context.user_data.get("withdraw_method")
    details = context.user_data.get("withdraw_details")

    # Зберігаємо у SQLite
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

    # Редагуємо те ж повідомлення, відображаючи фінальний текст
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="💸 Ваше звернення на виведення збережено! Очікуйте підтвердження від адміністратора.",
            reply_markup=nav_buttons()
        )

    # Очищаємо ключ, сценарій завершено
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── ConversationHandler для “Виведення коштів” ─────────────────────────────────
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
    Регіструємо ConversationHandler “виведення” у групі 0.
    """
    app.add_handler(withdraw_conv, group=0)
