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
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: користувач натиснув “💳 Мій профіль”.
    Питаємо у нього номер клубної картки.
    """
    # Якщо це CallbackQuery, відповідаємо на нього
    if update.callback_query:
        await update.callback_query.answer()

    # Відправляємо повідомлення з проханням ввести картку
    msg = await update.callback_query.message.reply_text(
        "💳 Введіть номер вашої клубної картки:",
        reply_markup=nav_buttons()
    )
    # Зберігаємо ID базового повідомлення, щоб редагувати його далі
    context.user_data['base_msg'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляємо введений номер картки:
      1) Надсилаємо адміну повідомлення з кнопкою “✅ Підтвердити картку” 
         і параметрами user_id та card.
      2) Інформуємо користувача, що запит відправлено адміністратору.
    """
    # Сам текст, який ввів користувач як картку
    card = update.message.text.strip()
    user_id = update.effective_user.id

    # 1) Створюємо кнопки для адміністратора
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
            "Перевірте наявність карти та натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # 2) Повідомляємо клієнта, що ми передали його запит адміну
    await update.message.reply_text(
        "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
        reply_markup=nav_buttons()
    )

    # Завершуємо діалог (ConversationHandler.END)
    return ConversationHandler.END

# ─── ConversationHandler для “Мій профіль” ────────────────────────────────────────
profile_conv = ConversationHandler(
    entry_points=[
        # Точна відповідність callback_data="client_profile"
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        # Після натискання “Мій профіль” бот чекає на звичайний текст із номером картки
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
    },
    fallbacks=[
        # Якщо користувач у середині сценарію натисне “Назад” або “Головне меню”,
        # повернемося до початку “Мій профіль”
        CallbackQueryHandler(start_profile, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(start_profile, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,   # важливо, щоб не відпускати чат між повідомленнями
)

def register_profile_handlers(app: Application) -> None:
    """
    Реєструє ConversationHandler для сценарію профілю.
    """
    app.add_handler(profile_conv, group=0)
