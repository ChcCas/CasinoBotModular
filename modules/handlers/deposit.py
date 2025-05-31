# modules/handlers/deposit.py

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
from modules.keyboards import nav_buttons, provider_buttons, payment_buttons
from modules.keyboards import PROVIDERS, PAYMENTS
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM
)

# МАПІНГ від відображених назв до внутрішніх
PROVIDER_MAPPING = {
    "СТАРА СИСТЕМА": "CHAMPION",
    "НОВА СИСТЕМА":  "SUPEROMATIC"
}

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "💸 Введіть суму для поповнення:"
    sent = await update.callback_query.message.reply_text(
        text, reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                if "Message is not modified" not in str(e):
                    raise
        return STEP_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="🎰 Оберіть провайдера:",
                reply_markup=provider_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    display_provider = update.callback_query.data  # "СТАРА СИСТЕМА" або "НОВА СИСТЕМА"
    internal_provider = PROVIDER_MAPPING.get(display_provider, display_provider)
    context.user_data["deposit_provider"] = internal_provider

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="💳 Оберіть метод оплати:",
                reply_markup=payment_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    payment_method = update.callback_query.data
    context.user_data["deposit_payment"] = payment_method

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="📎 Надішліть підтвердження (фото, документ або відео):",
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_DEPOSIT_FILE

async def process_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ftype = "photo"
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        ftype = "document"
        file_id = update.message.document.file_id
    elif update.message.video:
        ftype = "video"
        file_id = update.message.video.file_id
    else:
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text="❗️ Будь ласка, надішліть фото, документ або відео:",
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    raise
        return STEP_DEPOSIT_FILE

    context.user_data["deposit_file_type"] = ftype
    context.user_data["deposit_file_id"]   = file_id

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)
    ]])
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="✅ Все готово. Натисніть «Підтвердити».",
                reply_markup=kb
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_DEPOSIT_CONFIRM

async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = update.effective_user

    amount   = context.user_data.get("deposit_amount")
    provider = context.user_data.get("deposit_provider")
    payment  = context.user_data.get("deposit_payment")
    ftype    = context.user_data.get("deposit_file_type")
    file_id  = context.user_data.get("deposit_file_id")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO deposits 
              (user_id, username, amount, provider, payment_method, file_type, file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user.id, user.username, amount, provider, payment, ftype, file_id)
        )
        conn.commit()

    base_id = context.user_data.get("base_msg_id")
    final_text = "💸 Ваше поповнення збережено! Очікуйте підтвердження."
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=final_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

deposit_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(deposit_start, pattern=f"^{CB.DEPOSIT_START.value}$")
    ],
    states={
        STEP_DEPOSIT_AMOUNT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
        STEP_DEPOSIT_PROVIDER: [CallbackQueryHandler(process_deposit_provider, pattern="^(" + "|".join(PROVIDERS) + ")$")],
        STEP_DEPOSIT_PAYMENT:  [CallbackQueryHandler(process_deposit_payment, pattern="^(" + "|".join(PAYMENTS) + ")$")],
        STEP_DEPOSIT_FILE:     [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, process_deposit_file)],
        STEP_DEPOSIT_CONFIRM:  [CallbackQueryHandler(confirm_deposit, pattern=f"^{CB.DEPOSIT_CONFIRM.value}$")],
    },
    fallbacks=[
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_deposit_handlers(app: Application) -> None:
    app.add_handler(deposit_conv, group=0)
