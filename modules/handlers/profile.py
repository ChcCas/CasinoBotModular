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
from keyboards import nav_buttons, client_menu, main_menu
from states import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
)

def register_profile_handlers(app):
    # 1) Вхід у профіль / перевірка авторизації
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0,
    )
    # 2) Обробник logout
    app.add_handler(
        CallbackQueryHandler(profile_logout, pattern="^logout$"),
        group=1,
    )
    # 3) Введення картки (група 2)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=2,
    )
    # 4) Введення телефону (група 3)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=3,
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка 'Мій профіль': показуємо меню або починаємо авторизацію."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Дістаємо користувача з БД
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT card, is_authorized FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    # Якщо є і вже авторизований — показуємо меню профілю
    if row and row[1] == 1:
        await query.message.reply_text(
            "Вітаємо в особистому кабінеті!",
            reply_markup=client_menu(authorized=True)
        )
        return STEP_MENU

    # Інакше — починаємо нову авторизацію
    # Чистимо попередні дані
    context.user_data.pop("profile_card", None)
    await query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу картки (4–7 цифр)."""
    # Якщо вже авторизований — ігноруємо
    user_id = update.effective_user.id
    with sqlite3.connect(DB_NAME) as conn:
        auth = conn.execute(
            "SELECT is_authorized FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    if auth and auth[0] == 1:
        return

    text = update.message.text or ""
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
    """Обробка вводу телефону, запис у БД і завершення авторизації."""
    # Перевіряємо, що ми в процесі авторизації
    if "profile_card" not in context.user_data:
        return await _enter_profile(update, context)

    text = update.message.text or ""
    phone = re.sub(r"\D", "", text)

    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр, починаючи з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    card = context.user_data["profile_card"]
    user_id = update.effective_user.id

    # Записуємо в БД (створюємо/оновлюємо користувача)
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

    # Очищуємо тимчасові дані
    context.user_data.clear()

    await update.message.reply_text(
        "Ви успішно авторизовані! Ось ваше меню:",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU

async def profile_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопки 'Вийти' — знімаємо авторизацію й повертаємо в головне меню."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Оновлюємо БД
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "UPDATE users SET is_authorized = 0 WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

    # Чистимо контекст та повертаємо в головне меню
    context.user_data.clear()
    await query.message.reply_text(
        "Ви вийшли з профілю.",
        reply_markup=main_menu(is_admin=False)
    )
    return STEP_MENU
