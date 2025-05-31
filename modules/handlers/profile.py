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
from modules.db import authorize_card, search_user, get_user_history
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    1) Якщо є запис в clients з user_id і полем card → відразу показуємо меню авторизованого користувача.
    2) Якщо картки нема → просимо ввести номер картки.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id

    user_record = search_user(str(user_id))
    if user_record and user_record.get("card"):
        # Уже авторизований
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
                if "Message to edit not found" in str(e) or "Message is not modified" in str(e):
                    sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо картки нема — просимо ввести картку:
    prompt = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(prompt, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Після того, як клієнт вводить свій номер картки:
     – якщо такий номер уже в БД (поле card) → “авторизуємо” його (authorize_card) і показуємо меню авторизованого.
     – якщо картки в БД нема → відправляємо адміну запит з кнопкою “admin_confirm_card:<user_id>:<card>”.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    existing = search_user(card)
    if existing:
        # Якщо картка вже є в БД (в яку адміністратор її вніс раніше)
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
                    sent = await update.message.reply_text(text, reply_markup=keyboard)
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.message.reply_text(text, reply_markup=keyboard)
            context.user_data["base_msg_id"] = sent.message_id

        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # Якщо в БД такої картки нема — надсилаємо адміну запит із кнопкою
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

    # Інформуємо клієнта:
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
                sent = await update.message.reply_text(confirmation_text, reply_markup=nav_buttons())
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.message.reply_text(confirmation_text, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# Додаткові обробники для авторизованих клієнтів:
async def cashback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "🎁 Ваш кешбек: 0 UAH (поки що немає активних кешбеків)."
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
                sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        context.user_data["base_msg_id"] = sent.message_id

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = update.effective_user.id
    history = get_user_history(user_id)
    if not history:
        text = "📖 У вас ще немає жодних операцій."
    else:
        lines = ["📖 Останні операції:"]
        for op in history:
            t = op["timestamp"]
            amt = op["amount"]
            info = op["info"]
            if op["type"] == "deposit":
                lines.append(f"• [Депозит] {amt} UAH (провайдер: {info}) о {t}")
            else:
                lines.append(f"• [Виведення] {amt} UAH (метод: {info}) о {t}")
        text = "\n".join(lines)

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
                sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        context.user_data["base_msg_id"] = sent.message_id

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Клієнт виходить із «сесії» — ми просто очищаємо base_msg_id
    context.user_data.pop("base_msg_id", None)

    text = "🔒 Ви вийшли з профілю. Використовуйте “💳 Мій профіль” для повторної авторизації."
    keyboard = client_menu(is_authorized=False)
    sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
    context.user_data["base_msg_id"] = sent.message_id

async def help_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "ℹ️ Допомога:\n/start — перезапуск бота\n📲 Зверніться до підтримки, якщо є питання."
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
                sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
        context.user_data["base_msg_id"] = sent.message_id

# ConversationHandler для “Мій профіль”
profile_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
        STEP_MENU: [
            CallbackQueryHandler(cashback_handler, pattern=r"^cashback$"),
            CallbackQueryHandler(history_handler, pattern=r"^history$"),
            CallbackQueryHandler(logout_handler, pattern=r"^logout$"),
            CallbackQueryHandler(help_auth_handler, pattern=f"^{CB.HELP.value}$"),
            # решта кнопок (deposit_start, withdraw_start) — є у інших ConversationHandler
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
