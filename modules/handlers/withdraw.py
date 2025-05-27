# modules/handlers/withdraw.py

import sqlite3
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME
from keyboards import nav_buttons, payment_buttons
from states import STEP_MENU, STEP_PAYMENT, STEP_CONFIRM_FILE, STEP_CONFIRMATION

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Оберіть метод виведення коштів:", reply_markup=payment_buttons())
    return STEP_PAYMENT

async def withdraw_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data in ("back", "home"):
        return await withdraw_start(update, context)

    context.user_data["withdraw_method"] = q.data
    await q.message.reply_text("Завантажте файл підтвердження (фото/документ/відео):", reply_markup=nav_buttons())
    return STEP_CONFIRM_FILE

async def withdraw_process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file_msg"] = update.message
    await update.message.reply_text("Натисніть ✅, щоб підтвердити надсилання:", reply_markup=nav_buttons())
    return STEP_CONFIRMATION

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user   = update.effective_user
    method = context.user_data["withdraw_method"]
    file_msg = context.user_data["file_msg"]

    caption = f"Заявка на виведення:\nМетод: {method}"
    await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                method TEXT,
                file_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO withdrawals(user_id, username, method, file_type) VALUES (?,?,?,?)",
            (user.id, user.username or "", method, file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await q.message.reply_text("Ваша заявка на виведення надіслана!", reply_markup=nav_buttons())
    return STEP_MENU

def register_withdraw_handlers(app):
    app.add_handler(CallbackQueryHandler(withdraw_start, pattern="^withdraw$"), group=0)
    app.add_handler(CallbackQueryHandler(withdraw_process_payment, pattern="^(Карта|Криптопереказ)$"), group=1)
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, withdraw_process_file), group=1)
    app.add_handler(CallbackQueryHandler(withdraw_confirm, pattern="^confirm$"), group=1)
