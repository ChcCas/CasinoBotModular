import re
import sqlite3
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application
)
from modules.config import DB_NAME
from modules.keyboards import nav_buttons, payment_buttons
from modules.callbacks import CB
from modules.states import (
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
)
from datetime import datetime

async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вхід у сценарій «Вивести кошти» (callback_data="withdraw_start").
    Питаємо суму.
    """
    await update.callback_query.answer()
    text = "💳 Введіть суму для виведення:"
    sent = await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_AMOUNT

async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт вводить суму виведення.
    Переходимо до вибору методу виведення.
    """
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❗️ Введіть коректну суму:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount
    text = "Оберіть метод виведення:"
    sent = await update.message.reply_text(text, reply_markup=payment_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт обирає метод («Карта» або «Криптопереказ»).
    Запитуємо реквізити (номер картки / гаманець).
    """
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method
    await update.callback_query.answer()

    text = "💳 Введіть реквізити (номер картки або гаманець):"
    sent = await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт надсилає текст із реквізитами (рядок).
    Ми зберемо все в БД.
    """
    details = update.message.text.strip()
    user = update.effective_user
    user_id = user.id
    amount = context.user_data.get("withdraw_amount")
    method = context.user_data.get("withdraw_method")
    now = datetime.utcnow().isoformat()

    # Записуємо транзакцію у таблицю transactions
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (user_id, type, amount, info, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, "withdraw", amount, f"{method}: {details}", now)
    )
    conn.commit()
    conn.close()

    # Повідомляємо клієнта:
    text = "✅ Ваш запит на виведення збережено! Очікуйте підтвердження."
    keyboard = client_menu(is_authorized=True)
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except Exception as e:
            # Якщо неможливо відредагувати → просто відправимо нове
            sent = await update.message.reply_text(text, reply_markup=keyboard)
            context.user_data["base_msg_id"] = sent.message_id
    else:
        sent = await update.message.reply_text(text, reply_markup=keyboard)
        context.user_data["base_msg_id"] = sent.message_id

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

def register_withdraw_handlers(app: Application) -> None:
    withdraw_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_withdraw, pattern=f"^{CB.WITHDRAW_START.value}$")
        ],
        states={
            STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(process_withdraw_method, pattern="^(Карта|Криптопереказ)$")],
            STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True,
    )
    app.add_handler(withdraw_conv, group=0)
