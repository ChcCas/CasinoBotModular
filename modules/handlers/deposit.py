import re
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
from modules.db import get_user, save_user
from keyboards import nav_buttons, main_menu
from states import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD, STEP_PROFILE_ENTER_PHONE,
)

def register_profile_handlers(app):
    app.add_handler(CallbackQueryHandler(start_profile, pattern="^PROFILE_START$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone), group=1)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)
    if user:
        # вже авторизований
        await update.callback_query.message.reply_text(
            "Ви вже авторизовані! 👇",
            reply_markup=main_menu(is_admin=False, is_auth=True)
        )
        return STEP_MENU

    # починаємо авторизацію
    await update.callback_query.message.reply_text(
        "Введіть номер картки (4–7 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = re.sub(r"\D", "", update.message.text)
    if not (4 <= len(card) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути 4–7 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["card"] = card
    await update.message.reply_text(
        "Тепер введіть телефон (0XXXXXXXXX):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = re.sub(r"\D", "", update.message.text)
    if not (len(phone) == 10 and phone.startswith("0")):
        await update.message.reply_text(
            "Невірний телефон. Має бути 10 цифр, починається з 0.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    save_user(update.effective_user.id, context.user_data["card"], phone)
    await update.message.reply_text(
        "✅ Авторизація успішна!",
        reply_markup=main_menu(is_admin=False, is_auth=True)
    )
    return STEP_MENU
