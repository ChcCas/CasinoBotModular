from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application,
)
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    1) Якщо у clients є запис для цього user_id із полем `card` → показуємо меню авторизованого користувача.
    2) Якщо нема картки → запитуємо “💳 Введіть номер картки:”.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id

    # Перевіряємо, чи цього користувача вже є в базі з карткою
    user_record = search_user(str(user_id))
    if user_record and user_record.get("card"):
        # Користувач уже авторизований → показуємо меню авторизованого клієнта
        card = user_record["card"]
        text = (
            f"🎉 Ви вже авторизовані!\n"
            f"Ваша картка: {card}\n\n"
            "Оберіть дію:"
        )
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
                # Якщо не вдалося відредагувати (наприклад, нема повідомлення чи нічого не змінювалося),
                # просто висилаємо нове
                if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
                    sent = await update.callback_query.message.reply_text(
                        text,
                        reply_markup=keyboard
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.callback_query.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо користувача нема в БД або нема в нього картки→ запитуємо номер картки
    prompt = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(
        prompt,
        reply_markup=nav_buttons()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач увів свій номер картки:
    1) Перевіряємо, чи є ця картка в БД (search_user(card)):
       - Якщо є → “авторизуємо” (authorize_card), показуємо меню авторизованого.
       - Якщо немає → надсилаємо адміну запит “admin_confirm_card:<user_id>:<card>”.
    2) Редагуємо або надсилаємо користувачу підтвердження.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # Перевіряємо наявність картки в БД
    existing = search_user(card)
    if existing:
        # Якщо картка вже записана адміністратором
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
                if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
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

    # Якщо картки в БД немає — надсилаємо адміну запит із кнопкою підтвердження
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
            "Перевірте, і якщо вона є — натисніть «✅ Підтвердити картку»."
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
            if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
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

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── ConversationHandler для “Мій профіль” ────────────────────────────
profile_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
        # Меню авторизованого клієнта потім оброблюється окремо в STEP_MENU
    },
    fallbacks=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(start_profile, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler для сценарію “Мій профіль” (група=0).
    """
    app.add_handler(profile_conv, group=0)
