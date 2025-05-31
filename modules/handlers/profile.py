# modules/handlers/profile.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user
from modules.keyboards import nav_buttons
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    Запитуємо номер клубної картки.
    """
    if update.callback_query:
        await update.callback_query.answer()

    msg = await update.callback_query.message.reply_text(
        "💳 Введіть номер вашої клубної картки:",
        reply_markup=nav_buttons()
    )
    # Зберігаємо ID цього повідомлення (якщо пізніше треба редагувати)
    context.user_data['base_msg'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляємо текст, який ввів користувач (номер картки):
      1) Надсилаємо адміну повідомлення з кнопкою підтвердження
         (callback_data="admin_confirm_card:<user_id>:<card>").
      2) Повідомляємо клієнта, що запит відправлено.
      3) Закінчуємо сценарій (ConversationHandler.END).
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "✅ Підтвердити картку",
            callback_data=f"admin_confirm_card:{user_id}:{card}"
        )
    ]])
    # Надсилаємо адміну повідомлення
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"ℹ️ Користувач {update.effective_user.full_name} (ID {user_id})\n"
            f"ввів картку: {card}\n"
            "Перевірте, чи така картка є, і натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # Інформуємо клієнта
    await update.message.reply_text(
        "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
        reply_markup=nav_buttons()
    )

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
        # Якщо користувач натисне «Назад» або «Головне меню», завершуємо бесіду
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Реєструє profile_conv (ConversationHandler) у групі 0.
    """
    app.add_handler(profile_conv, group=0)
