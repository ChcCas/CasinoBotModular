# modules/handlers/deposit.py

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
from modules.keyboards import nav_buttons, provider_buttons, payment_buttons
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM
)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув «💰 Поповнити» (callback_data="deposit_start").
    Просимо ввести суму.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "💸 Введіть суму для поповнення:", 
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_AMOUNT: користувач вводить суму.
    Перевіряємо валідність, зберігаємо й просимо вибір провайдера.
    """
    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text(
            "❗️ Невірний формат суми. Спробуйте ще раз:",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    context.user_data["deposit_amount"] = amount
    # Далі – вибір провайдера
    await update.message.reply_text(
        "🎰 Оберіть провайдера:", 
        reply_markup=provider_buttons()
    )
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_PROVIDER: користувач натиснув на одну з кнопок провайдера
    (callback_data == назва провайдера, наприклад "🏆 CHAMPION").
    """
    await update.callback_query.answer()
    provider = update.callback_query.data
    context.user_data["deposit_provider"] = provider

    # Далі – вибір методу оплати
    await update.callback_query.message.reply_text(
        "💳 Оберіть метод оплати:", 
        reply_markup=payment_buttons()
    )
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_PAYMENT: користувач натиснув тему оплат (callback_data == "Карта" чи "Криптопереказ").
    """
    await update.callback_query.answer()
    payment_method = update.callback_query.data
    context.user_data["deposit_payment"] = payment_method

    # Далі – просимо надіслати фото/документ із підтвердженням
    await update.callback_query.message.reply_text(
        "📎 Надішліть підтвердження (фото, документ або відео):", 
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_FILE

async def process_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_FILE: користувач надсилає фото/документ/відео.
    Зберігаємо у тимчасовий контекст (можна зберегти file_id).
    Потім відправляємо клавіатуру із кнопкою “Підтвердити”.
    """
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
        await update.message.reply_text(
            "❗️ Будь ласка, надішліть фото, документ або відео.",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_FILE

    context.user_data["deposit_file_type"] = ftype
    context.user_data["deposit_file_id"]   = file_id

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити", 
                             callback_data=CB.DEPOSIT_CONFIRM.value)
    ]])
    await update.message.reply_text(
        "✅ Дякуємо! Натисніть «Підтвердити», щоб завершити поповнення.", 
        reply_markup=kb
    )
    return STEP_DEPOSIT_CONFIRM

async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_CONFIRM: користувач натиснув “✅ Підтвердити” (callback_data="deposit_confirm").
    Зберігаємо інформацію в БД і повідомляємо, що чекати підтвердження.
    """
    await update.callback_query.answer()
    user = update.effective_user

    # Беремо всю потрібну інформацію з context.user_data
    amount   = context.user_data.get("deposit_amount")
    provider = context.user_data.get("deposit_provider")
    payment  = context.user_data.get("deposit_payment")
    ftype    = context.user_data.get("deposit_file_type")
    file_id  = context.user_data.get("deposit_file_id")

    # Приклад збереження в SQLite (таблиця deposits має бути створена раніше)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO deposits (user_id, username, amount, provider, payment_method, file_type, file_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.username, amount, provider, payment, ftype, file_id)
        )
        conn.commit()

    await update.callback_query.message.reply_text(
        "💸 Ваше поповнення збережено! Очікуйте підтвердження від адміністратора.",
        reply_markup=nav_buttons()
    )
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
    """
    Реєструє deposit_conv (ConversationHandler) у групі 0.
    """
    app.add_handler(deposit_conv, group=0)
