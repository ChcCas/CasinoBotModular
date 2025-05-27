# modules/handlers/profile.py

import re
import sqlite3
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME
from keyboards import nav_buttons, client_menu
from states import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_CASHBACK_REQUEST,
    STEP_PROFILE_CASHBACK_CODE,
)


def register_profile_handlers(app):
    # 1) Натиск «Мій профіль» – вводимо карту
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0,
    )
    # 2) Введення картки
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1,
    )
    # 3) Введення телефону
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=1,
    )
    # 4) Запит кешбеку
    app.add_handler(
        CallbackQueryHandler(profile_cashback_request, pattern="^cashback$"),
        group=1,
    )
    # 5) Введення коду для кешбеку
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_cashback_code),
        group=1,
    )


async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт: запит номера картки."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD


async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу картки: знімаємо все, крім цифр, потім перевіряємо довжину."""
    text = update.message.text or ""
    # видаляємо пробіли, дефіси, інші символи
    card = re.sub(r"\D", "", text)

    if not (4 <= len(card) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр, без літер та пробілів.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    # зберігаємо "чистий" номер картки
    context.user_data["profile_card"] = card

    await update.message.reply_text(
        "Дякую! Тепер введіть номер телефону (повинен починатися з 0 та мати 10 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE


async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу телефону: перевірка формату 0XXXXXXXXX."""
    text = update.message.text or ""
    phone = re.sub(r"\D", "", text)

    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр, починаючи з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    # запис у базу
    card = context.user_data["profile_card"]
    user_id = update.effective_user.id

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                card TEXT,
                phone TEXT,
                is_authorized INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            INSERT INTO users(user_id, card, phone, is_authorized)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
              card=excluded.card,
              phone=excluded.phone,
              is_authorized=1
        """, (user_id, card, phone))
        conn.commit()

    context.user_data["is_authorized"] = True

    await update.message.reply_text(
        "Ви успішно авторизовані! Ось ваше меню:",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU


async def profile_cashback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Створюємо заявку на кешбек і відсилаємо адміну."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT card FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

    if not row:
        await query.message.reply_text(
            "Спочатку авторизуйтеся через «Мій профіль».",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    card = row[0]
    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🚨 Запит кешбеку від {update.effective_user.full_name} ({user_id}):\n"
            f"Картка: {card}\n\n"
            "Відповідайте на це повідомлення кодом."
        )
    )
    context.bot_data["last_cashback_request_id"] = msg.message_id

    await query.message.reply_text(
        "Введіть, будь ласка, 4-значний код для кешбеку:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_CASHBACK_CODE


async def profile_cashback_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введення коду кешбеку — відповідаємо адміну в thread."""
    text = update.message.text or ""
    code = re.sub(r"\D", "", text)

    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text(
            "Невірний код. Має бути 4 цифри.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_CASHBACK_CODE

    reply_to = context.bot_data.get("last_cashback_request_id")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔑 Код кешбеку від користувача: {code}",
        reply_to_message_id=reply_to
    )
    context.bot_data.pop("last_cashback_request_id", None)

    await update.message.reply_text(
        "Ваш код успішно надіслано адміністратору.",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU
