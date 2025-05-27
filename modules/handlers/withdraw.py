# modules/handlers/withdraw.py
import sqlite3, datetime
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from modules.config import ADMIN_ID, DB_NAME
from keyboards import nav_buttons
from states import STEP_WITHDRAW_AMOUNT, STEP_MENU

def register_withdraw_handlers(app):
    app.add_handler(CallbackQueryHandler(withdraw_start, pattern="^withdraw$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount), group=1)

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = sqlite3.connect(DB_NAME).execute(
        "SELECT card FROM users WHERE user_id=?", (update.effective_user.id,)
    ).fetchone()
    if not user:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "Вам потрібно спочатку авторизуватися (Мій профіль).",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть суму на вивід:",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    amount = text
    user = sqlite3.connect(DB_NAME).execute(
        "SELECT card FROM users WHERE user_id=?", (update.effective_user.id,)
    ).fetchone()[0]
    time_str = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    text = (
        f"💸 Вивід від {update.effective_user.full_name} ({update.effective_user.id}):\n"
        f"Картка клієнта: {user}\n"
        f"Сума: {amount}\n"
        f"🕒 {time_str}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Заявка на вивід відправлена адміну.", reply_markup=nav_buttons())
    return STEP_MENU
