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
    2) Перевіряємо в БД: якщо вже є запис з карткою → одразу показуємо меню авторизованого користувача.
       Інакше — запитуємо номер картки.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    user_record = search_user(str(user_id))

    if user_record and user_record.get("card"):
        # — Користувач уже авторизований (має картку в БД).
        card = user_record["card"]
        text = (
            f"🎉 Ви вже авторизовані!\n"
            f"Ваша картка: {card}\n\n"
            "Оберіть дію:"
        )
        keyboard = client_menu(is_authorized=True)

        base_id = context.user_data.get("base_msg_id")
        if base_id:
            # Працюємо з існуючим повідомленням, якщо воно ще є
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                msg = str(e)
                # Якщо повідомлення не знайдено або не зміненe — в обох випадках надсилаємо нове
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.callback_query.message.reply_text(
                        text,
                        reply_markup=keyboard
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    # Якщо якась інша помилка — кидаємо далі
                    raise
        else:
            # Якщо base_msg_id немає — надсилаємо нове
            sent = await update.callback_query.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо картки ще немає → запитуємо номер картки
    prompt = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(
        prompt,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Користувач ввів картку. Перевіряємо: чи вже є така картка в БД?
       - Якщо є → одразу авторизуємо, редагуємо одне повідомлення у клієнта.
       - Якщо немає → надсилаємо адміну запит і повідомляємо клієнту.
    2) У будь–якому разі завершуємо ConversationHandler (END).
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # 1) Перевіряємо, чи є картка в базі
    existing = search_user(card)
    if existing:
        # — Якщо картка знайдена (ймовірно, підтверджена адміністратором раніше)
        authorize_card(user_id, card)
        text = f"🎉 Картка {card} знайдена в базі. Ви успішно авторизовані."
        keyboard = client_menu(is_authorized=True)

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
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    # Якщо базового повідомлення вже немає або не змінилося — надсилаємо нове
                    sent = await update.message.reply_text(
                        text,
                        reply_markup=keyboard
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # 2) Якщо такої картки ще немає в БД → надсилаємо адміну запит на підтвердження
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
            "Перевірте в базі даних і натисніть «✅ Підтвердити картку»."
        ),
        reply_markup=kb
    )

    # 3) Редагуємо (або надсилаємо нове) повідомлення клієнта
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
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.message.reply_text(
                    confirmation_text,
                    reply_markup=nav_buttons()
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.message.reply_text(
            confirmation_text,
            reply_markup=nav_buttons()
        )
        context.user_data["base_msg_id"] = sent.message_id

    # 4) Завершуємо сценарій та очищуємо base_msg_id
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
        # Якщо клієнт натисне “Назад” / “Головне меню” під час уведення картки
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler (група 0), щоб обробити
    callback_data="client_profile" перед загальним навігаційним handler-ом.
    """
    app.add_handler(profile_conv, group=0)
