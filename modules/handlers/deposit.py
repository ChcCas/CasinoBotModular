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
from modules.keyboards import nav_buttons, provider_buttons, payment_buttons, PROVIDERS, PAYMENTS
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM
)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув “💰 Поповнити” (callback_data="deposit_start").
    Надсилаємо одне базове повідомлення та зберігаємо його message_id у user_data.
    """
    await update.callback_query.answer()

    text = "💸 Введіть суму для поповнення:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id

    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_AMOUNT: користувач вводить суму.
    Перевіряємо, чи це число. Якщо так — зберігаємо й редагуємо повідомлення,
    показуючи “Оберіть провайдера”. Якщо ні — знову просимо ввести коректну суму.
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
        return STEP_DEPOSIT_AMOUNT

    # Зберігаємо суму в контекст
    context.user_data["deposit_amount"] = amount

    # Редагуємо те ж повідомлення, тепер з клавіатурою вибору провайдера
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="🎰 Оберіть провайдера:",
            reply_markup=provider_buttons()
        )
    return STEP_DEPOSIT_PROVIDER

async def process_deposit_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_PROVIDER: користувач обрав провайдера (callback_data = одна з PROVIDERS).
    Зберігаємо його та редагуємо повідомлення, питаючи метод оплати.
    """
    await update.callback_query.answer()
    provider = update.callback_query.data
    context.user_data["deposit_provider"] = provider

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="💳 Оберіть метод оплати:",
            reply_markup=payment_buttons()
        )
    return STEP_DEPOSIT_PAYMENT

async def process_deposit_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_PAYMENT: користувач обрав метод оплати (callback_data = одна з PAYMENTS).
    Зберігаємо його та редагуємо повідомлення, запитуючи файл (фото/документ/відео).
    """
    await update.callback_query.answer()
    payment_method = update.callback_query.data
    context.user_data["deposit_payment"] = payment_method

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="📎 Надішліть підтвердження (фото, документ або відео):",
            reply_markup=nav_buttons()
        )
    return STEP_DEPOSIT_FILE

async def process_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_FILE: користувач надіслав фото/документ/відео.
    Зберігаємо file_type і file_id, редагуємо повідомлення, показуючи “Підтвердити”.
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
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="❗️ Будь ласка, надішліть фото, документ або відео:",
                reply_markup=nav_buttons()
            )
        return STEP_DEPOSIT_FILE

    # Зберігаємо тип та ідентифікатор файлу
    context.user_data["deposit_file_type"] = ftype
    context.user_data["deposit_file_id"]   = file_id

    # Створюємо клавіатуру з кнопкою “Підтвердити”
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)
    ]])
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="✅ Все готово. Натисніть «Підтвердити», щоб завершити поповнення.",
            reply_markup=kb
        )
    return STEP_DEPOSIT_CONFIRM

async def confirm_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_DEPOSIT_CONFIRM: користувач натиснув “✅ Підтвердити” (callback_data="deposit_confirm").
    Зберігаємо фінальну інформацію у таблицю deposits та повідомляємо клієнта.
    """
    await update.callback_query.answer()
    user = update.effective_user

    amount   = context.user_data.get("deposit_amount")
    provider = context.user_data.get("deposit_provider")
    payment  = context.user_data.get("deposit_payment")
    ftype    = context.user_data.get("deposit_file_type")
    file_id  = context.user_data.get("deposit_file_id")

    # Зберігаємо в SQLite
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """
            INSERT INTO deposits 
              (user_id, username, amount, provider, payment_method, file_type, file_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user.id, user.username, amount, provider, payment, ftype, file_id)
        )
        conn.commit()

    # Редагуємо те ж повідомлення, показуючи фінальний текст
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="💸 Ваше поповнення збережено! Очікуйте підтвердження від адміністратора.",
            reply_markup=nav_buttons()
        )

    # Очищаємо ключ, щоб при наступному запуску “Поповнення” з’явилося нове повідомлення
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── ConversationHandler для “Поповнення” ───────────────────────────────────────
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
    Регіструємо ConversationHandler “депозит” у групі 0.
    """
    app.add_handler(deposit_conv, group=0)
