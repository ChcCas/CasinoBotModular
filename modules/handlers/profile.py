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
    # 1) Вхід у профіль — запит карти
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0,
    )
    # 2) Обробка введення карти
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1,
    )
    # 3) Обробка введення телефону
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=1,
    )
    # 4) Запит кешбеку — надсилаємо адміну і просимо код
    app.add_handler(
        CallbackQueryHandler(profile_cashback_request, pattern="^cashback$"),
        group=1,
    )
    # 5) Обробка введення коду кешбеку
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_cashback_code),
        group=1,
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт сценарію — запит номера картки."""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    # лише цифри, довжина 4–7
    if not re.fullmatch(r"\d{4,7}", card):
        await update.message.reply_text(
            "Невірний формат картки. Має бути 4–7 цифр, без пробілів.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["profile_card"] = card
    await update.message.reply_text(
        "Введіть, будь ласка, номер телефону (починається з 0, всього 10 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    # починається з 0 та 9 цифр далі
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр, починаючи з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    card = context.user_data["profile_card"]
    # Зберігаємо в базу або оновлюємо
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
        """, (update.effective_user.id, card, phone))
        conn.commit()

    # Авторизуємо в user_data
    context.user_data["is_authorized"] = True

    # Повідомляємо користувача
    await update.message.reply_text(
        "Ви успішно авторизовані! Ось ваш профіль:",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU

async def profile_cashback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Клієнт натиснув «🎁 Кешбек» — висилаємо адміну заявку."""
    query = update.callback_query
    await query.answer()

    # Отримуємо з бази картку
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT card FROM users WHERE user_id = ?",
            (update.effective_user.id,)
        ).fetchone()

    card = row[0] if row else None
    if not card:
        await query.message.reply_text(
            "Спочатку авторизуйтеся через Мій профіль.",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # Надсилаємо адміну заявку
    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🚨 Клієнт {update.effective_user.full_name} ({update.effective_user.id})\n"
            f"хоче зняти кешбек.\n"
            f"Картка: {card}\n\n"
            "Будь ласка, відповідайте на це повідомлення кодом."
        )
    )
    # Зберігаємо message_id для «ланцюжка»
    context.bot_data["last_cashback_request_id"] = msg.message_id

    # Питаємо код
    await query.message.reply_text(
        "Будь ласка, введіть 4-значний код підтвердження:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_CASHBACK_CODE

async def profile_cashback_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text(
            "Невірний код. Має бути 4 цифри.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_CASHBACK_CODE

    # Відповідаємо адміну в ланцюжку
    reply_to = context.bot_data.get("last_cashback_request_id")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔑 Код для кешбеку: {code}",
        reply_to_message_id=reply_to
    )
    context.bot_data.pop("last_cashback_request_id", None)

    await update.message.reply_text(
        "Ваш код відправлено адміністратору. Чекайте підтвердження.",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU
