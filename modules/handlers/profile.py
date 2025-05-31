# modules/handlers/profile.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув “💳 Мій профіль”.
    Запитуємо номер клубної картки.
    """
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "💳 Введіть номер вашої клубної картки:",
        reply_markup=nav_buttons()
    )
    context.user_data['base_msg'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробка введеного номера картки:
     1) надсилаємо адміну повідомлення з кнопкою підтвердження;
     2) інформуємо користувача, що запит відправлено.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id

    # 1) Надсилаємо адміну запит із callback для підтвердження
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "✅ Підтвердити картку",
            callback_data=f"admin_confirm_card:{user_id}:{card}"
        )
    ]])
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"ℹ️ Користувач {update.effective_user.full_name} (ID {user_id})\n"
            f"ввів картку: {card}\n"
            "Перевірте наявність карти та натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # 2) Повідомляємо клієнта
    await update.message.reply_text(
        "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
        reply_markup=nav_buttons()
    )

    # Завершуємо сценарій
    return ConversationHandler.END

# ConversationHandler для “Мій профіль”
profile_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(start_profile, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,  # <-- Замість per_message=True
)

def register_profile_handlers(app: "Application") -> None:
    """
    Реєструє ConversationHandler для сценарію профілю.
    """
    app.add_handler(profile_conv, group=0)
