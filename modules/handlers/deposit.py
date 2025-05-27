# modules/handlers/deposit.py

import sqlite3, datetime
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from modules.config import ADMIN_ID, DB_NAME
from keyboards import provider_buttons, payment_buttons, nav_buttons
from states import (
    STEP_PROVIDER, STEP_PAYMENT, STEP_DEPOSIT_AMOUNT,
    STEP_GUEST_DEPOSIT_FILE, STEP_GUEST_DEPOSIT_CONFIRM,
    STEP_MENU
)
from modules.db import get_user

def register_deposit_handlers(app):
    app.add_handler(CallbackQueryHandler(deposit_start, pattern="^deposit$"), group=0)
    app.add_handler(CallbackQueryHandler(guest_deposit_start, pattern="^guest_deposit$"), group=1)
    app.add_handler(CallbackQueryHandler(deposit_with_card_start, pattern="^deposit_with_card$"), group=1)
    app.add_handler(CallbackQueryHandler(deposit_process_provider, pattern="^(" + "|".join(PROVIDERS) + ")$"), group=2)
    app.add_handler(CallbackQueryHandler(deposit_process_payment, pattern="^(Карта|Криптопереказ)$"), group=3)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_process_amount), group=4)
    # гость без карти
    app.add_handler(MessageHandler(filters.Document.ALL|filters.PHOTO|filters.VIDEO, guest_deposit_file), group=5)
    app.add_handler(CallbackQueryHandler(guest_deposit_confirm, pattern="^confirm_guest$"), group=6)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Виберіть варіант поповнення:",
        reply_markup=deposit_menu(user_id)
    )
    return STEP_PROVIDER

async def guest_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Будь ласка, завантажте файл підтвердження (скріншот/фото/відео):",
        reply_markup=nav_buttons()
    )
    return STEP_GUEST_DEPOSIT_FILE

async def guest_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["guest_file"] = update.message
    await update.message.reply_text(
        "Підтвердіть надсилання заявки адміну:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Надіслати", callback_data="confirm_guest")]])
    )
    return STEP_GUEST_DEPOSIT_CONFIRM

async def guest_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file_msg = context.user_data["guest_file"]
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    text = (
        f"🎮 Гість ({user.full_name}, {user.id}) хоче поповнити без карти\n"
        f"Картка клієнта: Ставити на нашу\n"
        f"Провайдер: Н/Д\n"
        f"🕒 {timestamp}"
    )
    await file_msg.copy_to(ADMIN_ID, caption=text)
    await update.callback_query.message.reply_text("Ваша заявка відправлена.", reply_markup=nav_buttons())
    return STEP_MENU

async def deposit_with_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # авторизований потік
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Оберіть провайдера:",
        reply_markup=deposit_menu(update.effective_user.id)
    )
    return STEP_PROVIDER

async def deposit_process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["provider"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Оберіть спосіб оплати:",
        reply_markup=payment_buttons()
    )
    return STEP_PAYMENT

async def deposit_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["payment"] = update.callback_query.data
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть суму поповнення:",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

async def deposit_process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    amount = text
    user = get_user(update.effective_user.id)
    card = user[1] if user else "Н/Д"
    provider = context.user_data["provider"]
    payment  = context.user_data["payment"]
    time_str = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    text = (
        f"🆕 Поповнення від {update.effective_user.full_name} ({update.effective_user.id}):\n"
        f"Картка клієнта: {card}\n"
        f"Провайдер: {provider}\n"
        f"Оплата: {payment}\n"
        f"Сума: {amount}\n"
        f"🕒 {time_str}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.message.reply_text("Заявка на поповнення відправлена адміну.", reply_markup=nav_buttons())
    return STEP_MENU
