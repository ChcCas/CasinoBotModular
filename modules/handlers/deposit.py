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
from modules.keyboards import PROVIDERS, PAYMENTS, nav_buttons, provider_buttons, payment_buttons
from modules.callbacks import CB
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM,
    STEP_MENU,
)

async def process_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник натискання “💰 Поповнити” (callback_data="deposit_start")"""
    await update.callback_query.answer()
    sent = await update.callback_query.message.reply_text(
        "💸 Введіть суму для поповнення:",
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник — користувач ввів суму поповнення."""
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть коректну суму (число):",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    sent = await update.message.reply_text(
        "🎰 Оберіть провайдера:",
        reply_markup=provider_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник вибору провайдера (callback_data = один із PROVIDERS)."""
    await update.callback_query.answer()
    provider_choice = update.callback_query.data
    context.user_data["deposit_provider"] = provider_choice

    sent = await update.callback_query.message.reply_text(
        "💳 Оберіть метод оплати:",
        reply_markup=payment_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник вибору методу оплати (callback_data = один із PAYMENTS)."""
    await update.callback_query.answer()
    payment_method = update.callback_query.data
    context.user_data["deposit_payment"] = payment_method

    sent = await update.callback_query.message.reply_text(
        "📎 Надішліть підтвердження (фото, документ або відео):",
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_FILE

async def process_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник завантаження файлу (фото/документ/відео)."""
    if update.message.photo:
        file_type = "photo"
    elif update.message.document:
        file_type = "document"
    elif update.message.video:
        file_type = "video"
    else:
        await update.message.reply_text(
            "❗️ Будь ласка, надішліть фото, документ або відео:",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_FILE

    context.user_data["deposit_file_type"] = file_type

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)],
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])
    sent = await update.message.reply_text(
        "✅ Якщо все вірно, натисніть “Підтвердити”:",
        reply_markup=kb
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_CONFIRM

async def process_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник натискання “✅ Підтвердити” (callback_data="deposit_confirm")."""
    await update.callback_query.answer()
    user = update.effective_user

    amount   = context.user_data.get("deposit_amount")
    provider = context.user_data.get("deposit_provider")
    payment  = context.user_data.get("deposit_payment")
    file_t   = context.user_data.get("deposit_file_type")

    # Зберігаємо в БД
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO deposits (user_id, username, amount, provider, payment, file_type) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.username, amount, provider, payment, file_t)
        )
        conn.commit()

    text = "💸 Поповнення збережено! Очікуйте підтвердження від адміністратора."
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

def register_deposit_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler для сценарію депозиту.
    """
    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(process_deposit_start, pattern=f"^{CB.DEPOSIT_START.value}$")
        ],
        states={
            STEP_DEPOSIT_AMOUNT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_DEPOSIT_PROVIDER: [CallbackQueryHandler(process_deposit_provider, pattern="^(" + "|".join(PROVIDERS) + ")$")],
            STEP_DEPOSIT_PAYMENT:  [CallbackQueryHandler(process_deposit_payment, pattern="^(" + "|".join(PAYMENTS) + ")$")],
            STEP_DEPOSIT_FILE:     [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, process_deposit_file)],
            STEP_DEPOSIT_CONFIRM:  [CallbackQueryHandler(process_deposit_confirm, pattern=f"^{CB.DEPOSIT_CONFIRM.value}$")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True,
    )
    app.add_handler(deposit_conv, group=0)
