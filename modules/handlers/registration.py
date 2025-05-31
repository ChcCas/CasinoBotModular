# modules/handlers/registration.py

import sqlite3
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import nav_buttons
from modules.states import (
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE
)

async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув «📝 Реєстрація» (callback_data="register").
    Питаємо ім'я.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📝 Введіть ваше ім’я:", 
        reply_markup=nav_buttons()
    )
    return STEP_REG_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_REG_NAME: користувач вводить ім'я.
    Перевіряємо (наприклад, не порожньо), зберігаємо і питаємо телефон.
    """
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text(
            "❗️ Ім’я не може бути порожнім. Спробуйте ще раз:",
            reply_markup=nav_buttons()
        )
        return STEP_REG_NAME

    context.user_data["reg_name"] = name
    await update.message.reply_text(
        "📞 Введіть номер телефону (формат 0XXXXXXXXX):", 
        reply_markup=nav_buttons()
    )
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_REG_PHONE: користувач вводить телефон.
    Перевіряємо, чи 10 цифр і починається з 0.
    """
    phone = update.message.text.strip()
    import re
    if not re.match(r"^0\d{9}$", phone):
        await update.message.reply_text(
            "❗️ Невірний формат номера. Спробуйте ще раз:", 
            reply_markup=nav_buttons()
        )
        return STEP_REG_PHONE

    context.user_data["reg_phone"] = phone
    await update.message.reply_text(
        "🔑 Введіть 4-значний код підтвердження:", 
        reply_markup=nav_buttons()
    )
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок STEP_REG_CODE: користувач вводить 4-значний код.
    Якщо OK – зберігаємо все в БД (таблиця registrations), повідомляємо про успіх.
    """
    code = update.message.text.strip()
    import re
    if not re.match(r"^\d{4}$", code):
        await update.message.reply_text(
            "❗️ Код має складатися з 4 цифр. Спробуйте ще раз:", 
            reply_markup=nav_buttons()
        )
        return STEP_REG_CODE

    user_id = update.effective_user.id
    name = context.user_data.get("reg_name")
    phone = context.user_data.get("reg_phone")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO registrations (user_id, name, phone, code) VALUES (?, ?, ?, ?)",
            (user_id, name, phone, code)
        )
        conn.commit()

    await update.message.reply_text(
        "✅ Реєстрація успішна! Ви можете продовжувати роботу з ботом.", 
        reply_markup=nav_buttons()
    )
    return ConversationHandler.END

registration_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(registration_start, pattern=f"^{CB.REGISTER.value}$")
    ],
    states={
        STEP_REG_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        STEP_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
        STEP_REG_CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_code)],
    },
    fallbacks=[
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_registration_handlers(app: Application) -> None:
    app.add_handler(registration_conv, group=0)
