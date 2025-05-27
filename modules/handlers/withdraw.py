# modules/handlers/withdraw.py

import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from modules.config import ADMIN_ID
from modules.db import get_user
from keyboards import nav_buttons, main_menu
from states import (
    STEP_WITHDRAW_START,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_CONFIRM,
    STEP_MENU,
)

def register_withdraw_handlers(app):
    # 1) Точка входу — тільки авторизовані клієнти
    app.add_handler(
        CallbackQueryHandler(withdraw_start, pattern="^WITHDRAW_START$"),
        group=0,
    )
    # 2) Клієнт вводить суму
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount),
        group=1,
    )
    # 3) Підтвердження і відправка адміну
    app.add_handler(
        CallbackQueryHandler(withdraw_confirm, pattern="^CONFIRM_WITHDRAW$"),
        group=2,
    )


async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник натискання кнопки 'Вивід коштів'.
    Перевіряємо, чи є клієнт в БД (тобто авторизований),
    і якщо так — пропонуємо ввести суму.
    """
    user_id = update.effective_user.id
    await update.callback_query.answer()

    row = get_user(user_id)
    if not row:
        # Якщо не авторизований — кидаємо назад у головне меню з проханням авторизуватися
        await update.callback_query.message.reply_text(
            "Ви ще не авторизовані. Будь ласка, спочатку натисніть «Мій профіль» та виконайте авторизацію.",
            reply_markup=main_menu(is_admin=False, is_auth=False),
        )
        return STEP_MENU

    # Запитуємо суму виводу
    await update.callback_query.message.reply_text(
        "Введіть суму для виведення:",
        reply_markup=nav_buttons(),
    )
    return STEP_WITHDRAW_AMOUNT


async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник вводу суми виводу.
    Перевіряємо валідність, зберігаємо в user_data і показуємо кнопку підтвердження.
    """
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        # Невірна сума
        await update.message.reply_text(
            "Невірна сума. Введіть позитивне число.",
            reply_markup=nav_buttons(),
        )
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = text

    # Показуємо кнопку «Підтвердити»
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити вивід", callback_data="CONFIRM_WITHDRAW")],
        [InlineKeyboardButton("◀️ Назад",            callback_data="BACK")],
        [InlineKeyboardButton("🏠 Головне меню",     callback_data="HOME")],
    ])
    await update.message.reply_text(
        f"Ви бажаєте вивести {text} грн. Підтвердіть заявку:",
        reply_markup=kb,
    )
    return STEP_WITHDRAW_CONFIRM


async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Після натискання «✅ Підтвердити вивід» надсилаємо адміну заяву
    і повертаємо клієнта в головне меню.
    """
    await update.callback_query.answer()

    user = update.effective_user
    row = get_user(user.id)
    card = row[1]  # з БД повертаємо (user_id, card, phone)
    amount = context.user_data.get("withdraw_amount")
    ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    # Формуємо текст заявки
    text = (
        f"💸 Вивід коштів від {user.full_name} ({user.id}):\n"
        f"Картка клієнта: {card}\n"
        f"Сума: {amount} грн\n"
        f"🕒 {ts}"
    )
    # Надсилаємо адміну
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    # Очищаємо збережену суму
    context.user_data.pop("withdraw_amount", None)

    # Повертаємо клієнта в меню
    await update.callback_query.message.reply_text(
        "Заявка на виведення відправлена адміну.",
        reply_markup=main_menu(is_admin=False, is_auth=True),
    )
    return STEP_MENU
