# modules/handlers/deposit.py

import sqlite3
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME
from keyboards import nav_buttons, provider_buttons, payment_buttons
from states import (
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_MENU,
)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть номер картки клієнта клубу:", reply_markup=nav_buttons()
    )
    return STEP_CLIENT_CARD

async def deposit_process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not card.isdigit() or not (4 <= len(card) <= 5):
        await update.message.reply_text("Невірний формат картки. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    context.user_data["card"] = card
    await update.message.reply_text("Оберіть провайдера:", reply_markup=provider_buttons())
    return STEP_PROVIDER

async def deposit_process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data in ("back", "home"):
        return await deposit_start(update, context)

    context.user_data["provider"] = q.data
    await q.message.reply_text("Оберіть метод оплати:", reply_markup=payment_buttons())
    return STEP_PAYMENT

async def deposit_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data in ("back", "home"):
        return await deposit_start(update, context)

    context.user_data["payment"] = q.data
    await q.message.reply_text("Завантажте файл підтвердження (фото/документ/відео):", reply_markup=nav_buttons())
    return STEP_CONFIRM_FILE

async def deposit_process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file_msg"] = update.message
    await update.message.reply_text("Натисніть ✅, щоб підтвердити надсилання:", reply_markup=nav_buttons())
    return STEP_CONFIRMATION

async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user     = update.effective_user
    card     = context.user_data["card"]
    provider = context.user_data["provider"]
    payment  = context.user_data["payment"]
    file_msg = context.user_data["file_msg"]

    caption = f"Заявка від клієнта:\nКартка: {card}\nПровайдер: {provider}\nМетод оплати: {payment}"
    await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                card TEXT,
                provider TEXT,
                payment TEXT,
                file_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO deposits(user_id, username, card, provider, payment, file_type) VALUES (?,?,?,?,?,?)",
            (user.id, user.username or "", card, provider, payment,
             file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await q.message.reply_text("Дякуємо! Вашу заявку надіслано.", reply_markup=nav_buttons())
    return STEP_MENU

def register_deposit_handlers(app):
    # старт флоу
    app.add_handler(CallbackQueryHandler(deposit_start, pattern="^deposit$"), group=0)
    # вибір провайдера
    app.add_handler(
        CallbackQueryHandler(deposit_process_provider, pattern="^(🏆 CHAMPION|🎰 SUPEROMATIC)$"),
        group=1
    )
    # вибір способу оплати
    app.add_handler(
        CallbackQueryHandler(deposit_process_payment, pattern="^(Карта|Криптопереказ)$"),
        group=1
    )
    # отримання файлу
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, deposit_process_file),
        group=1
    )
    # підтвердження
    app.add_handler(CallbackQueryHandler(deposit_confirm, pattern="^confirm$"), group=1)
