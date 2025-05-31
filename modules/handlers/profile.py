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
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок 1: користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    Надсилаємо одне базове повідомлення “Введіть номер картки” та зберігаємо message_id.
    """
    await update.callback_query.answer()

    text = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id

    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Крок 2: обробка введеного номеру картки.
    1) Відправляємо адміну повідомлення з кнопкою “Підтвердити картку”. 
    2) Редагуємо те саме повідомлення клієнта текстом “Запит відправлено”.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

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
            f"ℹ️ Користувач {full_name} (ID {user_id})\n"
            f"ввів картку: {card}\n"
            "Перевірте наявність карти та натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # 2) Редагуємо повідомлення клієнта (це ж саме, base_msg_id)
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
            reply_markup=nav_buttons()
        )
    else:
        sent = await update.message.reply_text(
            "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження.",
            reply_markup=nav_buttons()
        )
        context.user_data["base_msg_id"] = sent.message_id

    # Очищаємо базове повідомлення, бо сценарій завершено
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── Головний ConversationHandler для сценарію “Мій профіль” ────────────────────
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
        # “Назад” або “Головне меню” → повернутися до /start
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    # Використовуємо per_chat=True, щоб відстежувати стан у межах чату
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструємо scenario “Мій профіль” (profile_conv) у групі 0.
    """
    app.add_handler(profile_conv, group=0)
