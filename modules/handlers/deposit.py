# modules/handlers/deposit.py

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from modules.config import ADMIN_ID, DB_NAME

# ← вот тут поправка:
from db import get_user             # если get_user в корне, в db.py  
# from modules.db import get_user    # если вы действительно положили его в modules/db.py

from states import (
    STEP_PROVIDER, STEP_PAYMENT, STEP_DEPOSIT_AMOUNT,
    STEP_GUEST_DEPOSIT_FILE, STEP_GUEST_DEPOSIT_CONFIRM,
    STEP_MENU
)

def register_deposit_handlers(app):
    # 1) Общий вход в поток пополнения
    app.add_handler(CallbackQueryHandler(deposit_start, pattern="^deposit$"), group=0)
    # 2) Если гость (без карты)
    app.add_handler(CallbackQueryHandler(guest_deposit_start, pattern="^guest_deposit$"), group=1)
    # 3) Если авторизованный (с картой)
    app.add_handler(CallbackQueryHandler(deposit_with_card_start, pattern="^deposit_with_card$"), group=1)
    # 4) Выбор провайдера
    app.add_handler(
        CallbackQueryHandler(deposit_process_provider,
                             pattern="^(🏆 CHAMPION|🎰 SUPEROMATIC)$"),
        group=2
    )
    # 5) Выбор типа оплаты
    app.add_handler(
        CallbackQueryHandler(deposit_process_payment,
                             pattern="^(Карта|Криптопереказ)$"),
        group=3
    )
    # 6) Ввод суммы
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_process_amount), group=4)
    # 7) Гость загружает файл
    app.add_handler(MessageHandler(filters.Document.ALL|filters.PHOTO|filters.VIDEO,
                                  guest_deposit_file), group=5)
    # 8) Подтверждение гостевой заявки
    app.add_handler(CallbackQueryHandler(guest_deposit_confirm, pattern="^confirm_guest$"), group=6)


async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало потока пополнения: показываем варианты."""
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)

    buttons = []
    if user:
        buttons.append([InlineKeyboardButton("💳 Поповнити з картою", callback_data="deposit_with_card")])
    buttons.append([InlineKeyboardButton("🎮 Поповнити без карти", callback_data="guest_deposit")])
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])

    await update.callback_query.message.reply_text(
        "Виберіть варіант поповнення:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return STEP_PROVIDER


async def deposit_with_card_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Авторизованный пользователь: сначала провайдер."""
    await update.callback_query.answer()
    buttons = [
        [InlineKeyboardButton(p, callback_data=p)] for p in ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
    ]
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    await update.callback_query.message.reply_text(
        "Оберіть провайдера:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return STEP_PROVIDER


async def deposit_process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем выбор провайдера."""
    context.user_data["provider"] = update.callback_query.data
    await update.callback_query.answer()

    buttons = [
        [InlineKeyboardButton(p, callback_data=p)] for p in ["Карта", "Криптопереказ"]
    ]
    buttons.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    await update.callback_query.message.reply_text(
        "Оберіть спосіб оплати:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return STEP_PAYMENT


async def deposit_process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем выбор оплаты и просим ввести сумму."""
    context.user_data["payment"] = update.callback_query.data
    await update.callback_query.answer()

    buttons = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.callback_query.message.reply_text(
        "Введіть суму поповнення:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return STEP_DEPOSIT_AMOUNT


async def deposit_process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяем сумму и шлём админу заявку."""
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ])
        await update.message.reply_text("Невірна сума.", reply_markup=kb)
        return STEP_DEPOSIT_AMOUNT

    amount = text
    user = get_user(update.effective_user.id)
    card = user[1] if user else "Н/Д"
    provider = context.user_data["provider"]
    payment = context.user_data["payment"]
    ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    msg = (
        f"🆕 Поповнення від {update.effective_user.full_name} ({update.effective_user.id}):\n"
        f"Картка клієнта: {card}\n"
        f"Провайдер: {provider}\n"
        f"Оплата: {payment}\n"
        f"Сума: {amount}\n"
        f"🕒 {ts}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.message.reply_text("Заявка на поповнення відправлена адміну.", reply_markup=kb)
    return STEP_MENU


async def guest_deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поток гостя: загружаем файл."""
    await update.callback_query.answer()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.callback_query.message.reply_text(
        "Завантажте файл підтвердження (скрін/фото/відео):",
        reply_markup=kb
    )
    return STEP_GUEST_DEPOSIT_FILE


async def guest_deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем файл и предлагаем подтвердить."""
    context.user_data["guest_file"] = update.message
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Надіслати", callback_data="confirm_guest")]])
    await update.message.reply_text(
        "Підтвердіть надсилання адміну:",
        reply_markup=kb
    )
    return STEP_GUEST_DEPOSIT_CONFIRM


async def guest_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляем файл админу с подписью."""
    user = update.effective_user
    file_msg = context.user_data["guest_file"]
    ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    caption = (
        f"🎮 Гість ({user.full_name},{user.id}) поповнює без карти\n"
        f"Картка: Ставити на нашу\n"
        f"🕒 {ts}"
    )
    await file_msg.copy_to(ADMIN_ID, caption=caption)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.callback_query.message.reply_text("Заявка відправлена.", reply_markup=kb)
    return STEP_MENU
