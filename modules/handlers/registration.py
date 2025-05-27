# modules/handlers/registration.py

import re
import sqlite3
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters
from modules.config import ADMIN_ID, DB_NAME
from keyboards     import nav_buttons
from states        import STEP_REG_NAME, STEP_REG_PHONE, STEP_REG_CODE, STEP_MENU

async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть ім’я або нікнейм:", reply_markup=nav_buttons()
    )
    return STEP_REG_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["reg_name"] = name
    await update.message.reply_text(
        "Введіть номер телефону (формат 0XXXXXXXXX):", reply_markup=nav_buttons()
    )
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний формат. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_REG_PHONE

    name = context.user_data["reg_name"]
    context.user_data["reg_phone"] = phone

    # сообщаем админу
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Нова реєстрація:\nІм'я: {name}\nТелефон: {phone}"
    )

    # сохраняем в БД
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO registrations(user_id,name,phone) VALUES(?,?,?)",
            (update.effective_user.id, name, phone)
        )
        conn.commit()

    await update.message.reply_text(
        "Чекайте код підтвердження. Введіть 4-значний код:", reply_markup=nav_buttons()
    )
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код. Введіть 4 цифри:", reply_markup=nav_buttons())
        return STEP_REG_CODE

    name = context.user_data["reg_name"]
    # шлём админу код
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код підтвердження від {name} ({update.effective_user.id}): {code}"
    )

    await update.message.reply_text("Реєстрацію надіслано!", reply_markup=nav_buttons())
    return STEP_MENU

def register_registration_handlers(app):
    app.add_handler(CallbackQueryHandler(registration_start, pattern="^register$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),   group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),  group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),   group=1)
