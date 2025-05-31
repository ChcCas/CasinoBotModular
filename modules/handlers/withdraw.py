import re
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application,
)
from modules.config import ADMIN_ID, DB_NAME
from modules.keyboards import PAYMENTS, nav_buttons, payment_buttons
from modules.callbacks import CB
from modules.states import (
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
    STEP_MENU,
)

async def process_withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник натискання “💸 Вивести кошти” (callback_data="withdraw_start")."""
    await update.callback_query.answer()
    sent = await update.callback_query.message.reply_text(
        "💳 Введіть суму для виведення:",
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_AMOUNT

async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник — користувач ввів суму для виведення."""
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть коректну суму (число):",
            reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount
    sent = await update.message.reply_text(
        "🛡 Оберіть метод виведення:",
        reply_markup=payment_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник вибору методу виведення (callback_data = один із PAYMENTS)."""
    await update.callback_query.answer()
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method

    sent = await update.callback_query.message.reply_text(
        "💬 Введіть реквізити (номер картки або гаманець):",
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник — користувач ввів свої реквізити/деталі."""
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data=CB.WITHDRAW_CONFIRM.value)],
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])
    sent = await update.message.reply_text(
        "✅ Якщо все вірно, натисніть “Підтвердити”:",
        reply_markup=kb
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_WITHDRAW_CONFIRM

async def process_withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник натискання “✅ Підтвердити” (callback_data="withdraw_confirm")."""
    await update.callback_query.answer()
    user = update.effective_user

    amount   = context.user_data.get("withdraw_amount")
    method   = context.user_data.get("withdraw_method")
    details  = context.user_data.get("withdraw_details")

    # Зберігаємо в БД
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO withdrawals (user_id, username, amount, method, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username, amount, method, details)
        )
        conn.commit()

    text = "📄 Запит на виведення збережено! Очікуйте підтвердження від адміністратора."
    keyboard = nav_buttons()

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
                sent = await update.callback_query.message.reply_text(
                    text,
                    reply_markup=keyboard
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(
            text,
            reply_markup=keyboard
        )
        context.user_data["base_msg_id"] = sent.message_id

    return STEP_MENU

def register_withdraw_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler для сценарію виведення коштів.
    """
    withdraw_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(process_withdraw_start, pattern=f"^{CB.WITHDRAW_START.value}$")
        ],
        states={
            STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(process_withdraw_method, pattern="^(" + "|".join(PAYMENTS) + ")$")],
            STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
            STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(process_withdraw_confirm, pattern=f"^{CB.WITHDRAW_CONFIRM.value}$")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True,
    )
    app.add_handler(withdraw_conv, group=0)
