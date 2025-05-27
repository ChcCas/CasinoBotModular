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
)

def register_profile_handlers(app):
    """
    Реєструє хендлери для сценарію "Мій профіль":
      1) натискання кнопки – початок (група 0)
      2) введення картки (група 1)
      3) введення телефону (група 2)
    """
    # 1) Кнопка "Мій профіль" → вводимо картку
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0,
    )
    # 2) Обробник тексту для введення картки
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1,
    )
    # 3) Обробник тексту для введення телефону
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=2,
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Початок сценарію: просимо ввести номер картки.
    """
    await update.callback_query.answer()
    context.user_data.pop("profile_card", None)
    await update.callback_query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє введений текст як картку.
    Перевіряє, що це 4–7 цифр, і зберігає в context.user_data.
    """
    # Якщо вже є profile_card — ігноруємо цей хендлер
    if "profile_card" in context.user_data:
        return

    text = update.message.text or ""
    # Видаляємо все, крім цифр
    card = re.sub(r"\D", "", text)

    if not (4 <= len(card) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр, без літер та пробілів.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["profile_card"] = card
    await update.message.reply_text(
        "Дякую! Тепер введіть номер телефону (повинен починатися з 0 та містити 10 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє введений текст як телефон.
    Перевіряє формат 0XXXXXXXXX, записує в БД та показує меню авторизованого клієнта.
    """
    if "profile_card" not in context.user_data:
        # якщо картки немає, почнімо спочатку
        return await _enter_profile(update, context)

    text = update.message.text or ""
    phone = re.sub(r"\D", "", text)

    # Перевіряємо 0 + 9 цифр
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр, починаючи з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    card = context.user_data["profile_card"]
    user_id = update.effective_user.id

    # Запис у SQLite
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

    # Очищуємо
    context.user_data.clear()

    # Відповідаємо та показуємо меню авторизованого клієнта
    await update.message.reply_text(
        "Ви успішно авторизовані! Ось ваше меню:",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU
