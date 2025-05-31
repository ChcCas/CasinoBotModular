# modules/handlers/profile.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
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
    Крок 1: користувач натиснув “💳 Мій профіль”.
    Надсилаємо базове повідомлення “Введіть номер картки” і зберігаємо message_id.
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
    Крок 2: користувач вводить номер картки.
    1) Надсилаємо адміну запит із кнопкою підтвердження.
    2) Редагуємо те саме повідомлення клієнта: “Запит відправлено адміністратору…”.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # 1) Надсилаємо адміну повідомлення з підтвердженням
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

    # 2) Редагуємо базове повідомлення клієнта
    base_id = context.user_data.get("base_msg_id")
    new_text = "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження."
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=new_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        sent = await update.message.reply_text(
            new_text,
            reply_markup=nav_buttons()
        )
        context.user_data["base_msg_id"] = sent.message_id

    # Завершуємо сценарій, очищаємо base_msg_id
    context.user_data.pop("base_msg_id", None)
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
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    app.add_handler(profile_conv, group=0)
