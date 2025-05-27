# modules/handlers/deposit.py

import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from modules.config import ADMIN_ID, DB_NAME
from modules.db import get_user

from states import (
    STEP_PROVIDER, STEP_PAYMENT, STEP_DEPOSIT_AMOUNT,
    STEP_GUEST_DEPOSIT_FILE, STEP_GUEST_DEPOSIT_CONFIRM,
    STEP_MENU
)

def register_deposit_handlers(app):
    # Основной вход в поток пополнения
    app.add_handler(
        CallbackQueryHandler(deposit_start, pattern="^deposit$"),
        group=0
    )
    # Гость без карты
    app.add_handler(
        CallbackQueryHandler(guest_deposit_start, pattern="^guest_deposit$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(deposit_with_card_start, pattern="^deposit_with_card$"),
        group=1
    )
    # Выбор провайдера (для обоих потоков после deposit_with_card_start)
    app.add_handler(
        CallbackQueryHandler(deposit_process_provider, pattern="^(" + "|".join(["🏆 CHAMPION","🎰 SUPEROMATIC"]) + ")$"),
        group=2
    )
    # Выбор способа оплаты
    app.add_handler(
        CallbackQueryHandler(deposit_process_payment, pattern="^(Карта|Криптопереказ)$"),
        group=3
    )
    # Ввод суммы
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_process_amount),
        group=4
    )
    # Гость загружает файл
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, guest_deposit_file),
        group=5
    )
    # Подтверждение гостевой заявки
    app.add_handler(
        CallbackQueryHandler(guest_deposit_confirm, pattern="^confirm_guest$"),
        group=6
    )

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт потока пополнения: если пользователь в БД — два варианта, иначе только гостевое."""
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)
    buttons = []
    if user:
        # авторизованный
        buttons.append([InlineKeyboardButton("💳 Поповнити з картою", callback_data="deposit_with_card")])
    # гостевой
    buttons.append([InlineKeyboardButton("🎮 Поповнити без карти", callback_data="guest_deposit")])
    # навигация
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    kb = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text(
        "Виберіть варіант поповнення:",
        reply_markup=kb
    )
    return STEP_PROVIDER

async def deposit_with_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поток авторизованного пополнения: сначала провайдер."""
    await update.callback_query.answer()
    buttons = [
        [InlineKeyboardButton(p, callback_data=p)] for p in ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
    ]
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    kb = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text(
        "Оберіть провайдера:",
        reply_markup=kb
    )
    return STEP_PROVIDER

async def deposit_process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем провайдера и просим способ оплаты."""
    context.user_data["provider"] = update.callback_query.data
    await update.callback_query.answer()

    buttons = [
        [InlineKeyboardButton(p, callback_data=p)] for p in ["Карта", "Криптопереказ"]
    ]
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    kb = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text(
        "Оберіть спосіб оплати:",
        reply_markup=kb
    )
    return STEP_PAYMENT

async def deposit_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем способ оплаты и просим сумму."""
    context.user_data["payment"] = update.callback_query.data
    await update.callback_query.answer()
    buttons = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    kb = InlineKeyboardMarkup(buttons)

    await update.callback_query.message.reply_text(
        "Введіть суму поповнення:",
        reply_markup=kb
    )
    return STEP_DEPOSIT_AMOUNT

async def deposit_process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем сумму и отправляем заявку админу."""
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        # неверная сумма
        buttons = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        kb = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Невірна сума.", reply_markup=kb)
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

    buttons = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    kb = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("Заявка на поповнення відправлена адміну.", reply_markup=kb)
    return STEP_MENU

async def guest_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поток гостевого пополнения: просим загрузить файл."""
    await update.callback_query.answer()
    buttons = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    kb = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.reply_text(
        "Будь ласка, завантажте файл підтвердження (скріншот/фото/відео):",
        reply_markup=kb
    )
    return STEP_GUEST_DEPOSIT_FILE

async def guest_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем файл в user_data и предлагаем подтвердить."""
    context.user_data["guest_file"] = update.message
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Надіслати", callback_data="confirm_guest")
    ]])
    await update.message.reply_text(
        "Підтвердіть надсилання заявки адміну:",
        reply_markup=kb
    )
    return STEP_GUEST_DEPOSIT_CONFIRM

async def guest_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляем файл админу с нужным подписью."""
    user = update.effective_user
    file_msg = context.user_data["guest_file"]
    timestamp = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    caption = (
        f"🎮 Гість ({user.full_name}, {user.id}) хоче поповнити без карти\n"
        f"Картка клієнта: Ставити на нашу\n"
        f"Провайдер: Н/Д\n"
        f"🕒 {timestamp}"
    )
    await file_msg.copy_to(ADMIN_ID, caption=caption)

    buttons = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    kb = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.reply_text(
        "Ваша заявка відправлена.", reply_markup=kb
    )
    return STEP_MENU
