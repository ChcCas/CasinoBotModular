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
    Application
)
from modules.config import DB_NAME
from modules.keyboards import nav_buttons, provider_buttons, payment_buttons
from modules.callbacks import CB
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM,
)
from datetime import datetime

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Вхід у сценарій «Поповнити» (callback_data="deposit_start").
    Питаємо суму.
    """
    await update.callback_query.answer()
    text = "💸 Введіть суму для поповнення:"
    sent = await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт вводить суму.
    Переходимо до вибору провайдера.
    """
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❗️ Введіть коректну суму:", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    context.user_data["amount"] = amount
    text = "🎰 Оберіть провайдера:"
    sent = await update.message.reply_text(text, reply_markup=provider_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт обирає провайдера (“СТАРА СИСТЕМА” або “НОВА СИСТЕМА”).
    Зберігаємо це, переходимо до вибору методу оплати.
    """
    provider = update.callback_query.data  # тут “СТАРА СИСТЕМА” або “НОВА СИСТЕМА”
    context.user_data["provider"] = provider
    await update.callback_query.answer()

    text = "💳 Оберіть метод оплати:"
    sent = await update.callback_query.message.reply_text(text, reply_markup=payment_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт обирає метод оплати (“Карта” або “Криптопереказ”).
    Питаємо суму ще раз (якщо потрібні реквізити), 
    але ми вже маємо суму, тому переходимо просто до запиту файлу.
    """
    payment = update.callback_query.data
    context.user_data["payment"] = payment
    await update.callback_query.answer()

    text = "📎 Надішліть підтвердження (фото, документ або відео):"
    sent = await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_FILE

async def process_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт надсилає фото/документ/відео підтвердження.
    Переходимо до фінального підтвердження.
    """
    # Ми просто зберемо тип файлу, а потім вставимо у БД
    if update.message.photo:
        ftype = "photo"
    elif update.message.document:
        ftype = "document"
    elif update.message.video:
        ftype = "video"
    else:
        ftype = "unknown"

    context.user_data["file_type"] = ftype

    kb = [
        [InlineKeyboardButton("✅ Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)],
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ]
    text = "✅ Натисніть підтвердити:"
    sent = await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_DEPOSIT_CONFIRM

async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Клієнт натискає «✅ Підтвердити» фінальну кнопку.
    Ми зберігаємо транзакцію в таблиці transactions.
    """
    await update.callback_query.answer()
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    card = context.user_data.get("amount")   # приміром, зберегли суму
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    amount = context.user_data.get("amount")
    ftype = context.user_data.get("file_type")
    now = datetime.utcnow().isoformat()

    # Записуємо транзакцію
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (user_id, type, amount, info, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user_id, "deposit", amount, f"{provider}/{payment}", now)
    )
    conn.commit()
    conn.close()

    # Повідомляємо клієнта:
    text = "💸 Поповнення збережено! Очікуйте підтвердження."
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
        except BadRequest as e:
            if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
                sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        context.user_data["base_msg_id"] = sent.message_id

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

def register_deposit_handlers(app: Application) -> None:
    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_deposit, pattern=f"^{CB.DEPOSIT_START.value}$")
        ],
        states={
            STEP_DEPOSIT_AMOUNT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_DEPOSIT_PROVIDER: [CallbackQueryHandler(process_deposit_provider, pattern="^(СТАРА СИСТЕМА|НОВА СИСТЕМА)$")],
            STEP_DEPOSIT_PAYMENT:  [CallbackQueryHandler(process_deposit_payment, pattern="^(Карта|Криптопереказ)$")],
            STEP_DEPOSIT_FILE:     [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, process_deposit_file)],
            STEP_DEPOSIT_CONFIRM:  [CallbackQueryHandler(confirm_deposit, pattern=f"^{CB.DEPOSIT_CONFIRM.value}$")],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
        ],
        per_chat=True,
    )
    app.add_handler(deposit_conv, group=0)
