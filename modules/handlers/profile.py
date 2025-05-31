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
    1) Користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    2) Перевіряємо в БД: якщо вже є запис про цього user_id → користувач авторизований, 
       редагуємо / надсилаємо повідомлення з інформацією та клавіатурою для авторизованого користувача.
    3) Якщо запису нема → запитуємо номер картки.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    user_record = search_user(str(user_id))  # шукаємо за user_id

    if user_record and user_record.get("card"):
        # Користувач вже авторизований: показуємо єдине повідомлення із меню авторизованого користувача
        card = user_record["card"]
        text = (
            f"🎉 Ви вже авторизовані!\n"
            f"Ваша картка: {card}\n\n"
            "Оберіть дію:"
        )
        keyboard = client_menu(is_authorized=True)

        # Якщо є base_msg_id — редагуємо його; інакше — надсилаємо нове повідомлення
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                # Ігноруємо помилку, якщо повідомлення не змінилося
                if "Message is not modified" not in str(e):
                    raise
        else:
            sent = await update.callback_query.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо користувача ще нема в БД (або нема картки) → запитуємо номер картки
    text = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Користувач вводить номер картки (MessageHandler).
    2) Перевіряємо одразу: чи вже є ця картка в БД (за унікальним номером)? 
       - Якщо є запис із такою карткою, збережений раніше адміном → авторизуємо користувача одразу.
       - Інакше → надсилаємо адміну повідомлення з кнопкою підтвердження. 
    3) Повідомляємо клієнта, що запит відправлено адміністратору, якщо це нова картка.
    4) Завершуємо сценарій.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # Перевіряємо, чи вже існує в БД запис про цю картку
    existing = search_user(card)  # шукаємо за номером картки
    if existing:
        # Якщо картка вже є (ймовірно, адмін підтвердив раніше) – авторизуємо
        authorize_card(user_id, card)  # переконуємося, що user_id зберігся під цим card
        text = f"🎉 Картка {card} знайдена в базі. Ви успішно авторизовані."
        keyboard = client_menu(is_authorized=True)

        # Редагуємо (або надсилаємо) єдине повідомлення
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    raise
        else:
            sent = await update.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        # Завершуємо сценарій
        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # Якщо картки ще нема → надсилаємо адміну запит на підтвердження картки
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

    # Інформуємо клієнта, що запит відправлено адміністратору
    confirmation_text = "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження."
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=confirmation_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        sent = await update.message.reply_text(
            confirmation_text,
            reply_markup=nav_buttons()
        )
        context.user_data["base_msg_id"] = sent.message_id

    # Завершуємо сценарій та очищуємо base_msg_id
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
        # Якщо клієнт натис «Назад» або «Головне меню» під час введення картки —
        # завершуємо сценарій без помилок
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Реєструє ConversationHandler для сценарію “Мій профіль” (група 0),
    щоб обробити callback_data="client_profile" до загального навігаційного handler.
    """
    app.add_handler(profile_conv, group=0)
