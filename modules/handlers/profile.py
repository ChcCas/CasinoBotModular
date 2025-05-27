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
    # 1) Вхід у профіль
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0
    )
    # 2) Введення картки → група 1
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1
    )
    # 3) Введення телефону → група 2
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=2
    )
    # 4) Вихід із профілю
    app.add_handler(
        CallbackQueryHandler(profile_logout, pattern="^logout$"),
        group=3
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник кнопки «Мій профіль»."""
    query = update.callback_query
    await query.answer()

    # Перевіряємо в БД, чи вже є авторизація
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT card, phone FROM users WHERE user_id = ?", (query.from_user.id,)
        ).fetchone()

    if row:
        # Користувач вже авторизований
        await query.message.reply_text(
            "Вітаю! Ви вже в особистому кабінеті.",
            reply_markup=client_menu(authorized=True)
        )
        return STEP_MENU

    # Інакше — просимо картку
    context.user_data.pop("profile_card", None)
    await query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу картки (4–7 цифр)."""
    # тільки тоді, коли ми в стані STEP_PROFILE_ENTER_CARD
    text = re.sub(r"\D", "", update.message.text or "")
    if not (4 <= len(text) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["profile_card"] = text
    await update.message.reply_text(
        "Дякую! Тепер введіть номер телефону (10 цифр, починається з 0):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу телефону (0XXXXXXXXX)."""
    # Переконаємося, що ми дійсно перейшли сюди після картки
    if "profile_card" not in context.user_data:
        return await _enter_profile(update, context)

    phone = re.sub(r"\D", "", update.message.text or "")
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр, починається з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    # Зберігаємо в БД
    user_id = update.effective_user.id
    card    = context.user_data["profile_card"]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   INTEGER PRIMARY KEY,
                card      TEXT    NOT NULL,
                phone     TEXT    NOT NULL
            )
        """)
        conn.execute("""
            INSERT INTO users(user_id, card, phone)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              card = excluded.card,
              phone = excluded.phone
        """, (user_id, card, phone))
        conn.commit()

    # Очищаємо тимчасові дані
    context.user_data.pop("profile_card", None)

    await update.message.reply_text(
        "Ви успішно авторизовані!",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU

async def profile_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопки «Вийти»."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()

    # Повертаємо до головного меню
    await query.message.reply_text(
        "Ви вийшли з профілю.",
        reply_markup=main_menu(is_admin=False)
    )
    return STEP_MENU
