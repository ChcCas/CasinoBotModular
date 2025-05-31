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
from modules.keyboards import nav_buttons
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "💳 Введіть номер вашої клубної картки:",
        reply_markup=nav_buttons()
    )
    context.user_data['base_msg'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    user_id = update.effective_user.id

    # Надсилаємо адміну запит
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

    # Інформуємо користувача
    await update.message.reply_text(
        "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
        reply_markup=nav_buttons()
    )

    # Завершуємо розмову
    return ConversationHandler.END

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
    per_message=True,
)
