# modules/handlers/profile.py

import re
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.db import get_user, save_user
from keyboards import nav_buttons, client_menu
from states import (
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_MENU,
)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Точка входу в сценарій 'Мій профіль'."""
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)

    # Якщо вже авторизований — показуємо меню авторизованого клієнта
    if user:
        await update.callback_query.message.reply_text(
            "Ви вже авторизовані 👇",
            reply_markup=client_menu(is_authorized=True),
        )
        return STEP_MENU

    # Інакше — просимо ввести картку
    await update.callback_query.message.reply_text(
        "Введіть номер картки (4–7 цифр):",
        reply_markup=nav_buttons(),
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка ввод у картки (4–7 цифр)."""
    card = re.sub(r"\D", "", update.message.text)
    if not (4 <= len(card) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр.",
            reply_markup=nav_buttons(),
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["card"] = card
    await update.message.reply_text(
        "Тепер введіть номер телефону (0XXXXXXXXX):",
        reply_markup=nav_buttons(),
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вводу телефону (10 цифр, починається з 0)."""
    phone = re.sub(r"\D", "", update.message.text)
    if not (len(phone) == 10 and phone.startswith("0")):
        await update.message.reply_text(
            "Невірний формат телефону. Має бути 10 цифр і починатися з 0.",
            reply_markup=nav_buttons(),
        )
        return STEP_PROFILE_ENTER_PHONE

    # Зберігаємо у базу і відкриваємо меню авторизованого клієнта
    save_user(update.effective_user.id, context.user_data["card"], phone)
    await update.message.reply_text(
        "✅ Авторизація успішна!",
        reply_markup=client_menu(is_authorized=True),
    )
    return STEP_MENU

def register_profile_handlers(app):
    """Реєструє ConversationHandler для профілю."""
    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_profile, pattern="^client_profile$"),
        ],
        states={
            STEP_PROFILE_ENTER_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card)
            ],
            STEP_PROFILE_ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone)
            ],
            # Після авторизації повертаємося в STEP_MENU
            STEP_MENU: []
        },
        fallbacks=[
            # дозволяємо знову запустити авторизацію, якщо користувач натисне кнопку «Мій профіль»
            CallbackQueryHandler(start_profile, pattern="^client_profile$")
        ],
        allow_reentry=True
    )
    app.add_handler(conv)