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
from modules.states import STEP_FIND_CARD_PHONE

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    2) Надсилаємо єдине повідомлення “Введіть номер вашої клубної картки:” + клавіатуру “Назад/Головне меню”.
    3) Зберігаємо message_id у context.user_data["base_msg_id"].
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
    1) Обробка введеного номера картки (MessageHandler).
    2) Надсилаємо адміну повідомлення з кнопкою підтвердження:
       callback_data = f"admin_confirm_card:{user_id}:{card}"
    3) Редагуємо (або надсилаємо, якщо base_msg_id відсутній) повідомлення клієнта
       з текстом “Ваш запит відправлено адміністратору. Очікуйте підтвердження.” + nav_buttons().
    4) Очищаємо context.user_data["base_msg_id"] і завершуємо сценарій (ConversationHandler.END).
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # 1) Надсилаємо адміну запит із callback-посиланням для підтвердження
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
            "Перевірте в базі даних і, якщо все правильно, натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # 2) Редагуємо базове повідомлення клієнта (або надсилаємо нове, якщо base_msg_id відсутній)
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
            # Ігноруємо помилку, якщо повідомлення не змінилося
            if "Message is not modified" not in str(e):
                raise
    else:
        sent = await update.message.reply_text(
            new_text,
            reply_markup=nav_buttons()
        )
        context.user_data["base_msg_id"] = sent.message_id

    # 3) Очищаємо base_msg_id, бо сценарій завершився
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── ConversationHandler для сценарію “Мій профіль” ────────────────────────────
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
        # Якщо клієнт натисне “Назад” або “Головне меню” під час уведення картки,
        # завершуємо сценарій без помилок.
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструє profile_conv у групі 0, щоб цей ConversationHandler обробив  
    callback_data="client_profile" раніше за загальний navigation handler.
    """
    app.add_handler(profile_conv, group=0)
