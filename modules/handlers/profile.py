# modules/handlers/profile.py
import re
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from modules.db import get_user, save_user
from modules.keyboards import nav_buttons, main_menu
from modules.states import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник початку прив’язки профілю"""
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)

    if user:
        # вже авторизований
        await update.callback_query.message.reply_text(
            "Ви вже авторизовані 👇",
            reply_markup=main_menu(is_admin=False, is_auth=True),
        )
        return STEP_MENU

    # новий користувач → починаємо авторизацію
    await update.callback_query.message.reply_text(
        "Введіть номер картки (4–7 цифр):",
        reply_markup=nav_buttons(),
    )
    return STEP_PROFILE_ENTER_CARD


async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник введення номера картки"""
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
    """Обробник введення номера телефону"""
    phone = re.sub(r"\D", "", update.message.text)

    if not (len(phone) == 10 and phone.startswith("0")):
        await update.message.reply_text(
            "Невірний телефон. Має бути 10 цифр і починатися з 0.",
            reply_markup=nav_buttons(),
        )
        return STEP_PROFILE_ENTER_PHONE

    # Зберігаємо користувача
    save_user(update.effective_user.id, context.user_data["card"], phone)

    await update.message.reply_text(
        "✅ Авторизація успішна!",
        reply_markup=main_menu(is_admin=False, is_auth=True),
    )
    return STEP_MENU


def register_profile_handlers(app):
    """Реєструє ConversationHandler для профілю"""
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_profile, pattern="^client_profile$")],
        states={
            STEP_PROFILE_ENTER_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card)
            ],
            STEP_PROFILE_ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone)
            ],
            STEP_MENU: []  # можна залишити пустим: подальші колбеки обробляють меню окремо
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(conv)
