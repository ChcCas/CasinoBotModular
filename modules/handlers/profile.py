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
from modules.db import search_user, authorize_card
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    1) Якщо в clients є запис з валідною карткою → показуємо меню авторизованого.
    2) Інакше → запитуємо “💳 Введіть номер картки:”.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # 1) Шукаємо за user_id у БД (якщо адміністратор раніше підтвердив картку)
    user_record = search_user(str(user_id))
    if user_record and user_record.get("card"):
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
                    chat_id=chat_id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                msg = str(e).lower()
                if ("message to edit not found" in msg) or ("message is not modified" in msg):
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

    # 2) Якщо картки немає або користувача не знайдено — запитуємо номер картки
    prompt = "💳 Введіть номер вашої клубної картки:"
    keyboard = nav_buttons()
    base_id = context.user_data.get("base_msg_id")

    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=prompt,
                reply_markup=keyboard
            )
        except BadRequest as e:
            msg = str(e).lower()
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
                sent = await update.callback_query.message.reply_text(
                    prompt,
                    reply_markup=keyboard
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(
            prompt,
            reply_markup=keyboard
        )
        context.user_data["base_msg_id"] = sent.message_id

    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач увів свій номер картки:
    1) Якщо така картка є в БД → авторизуємо, показуємо меню авторизованого.
    2) Якщо немає → надсилаємо адміну запит з callback_data="admin_confirm_card:<user_id>:<card>".
    3) Змінюємо (або надсилаємо) повідомлення клієнту:
       - у разі успіху — меню авторизованого;
       - у разі запиту — текст “Ваш запит відправлено адміністратору”.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    full_name = update.effective_user.full_name

    # 1) Перевірка: чи вже існує така картка у clients
    existing = search_user(card)
    if existing:
        # — Якщо картка знайдена (адміністратор підтвердив раніше)
        authorize_card(user_id, card)
        text = f"🎉 Картка {card} знайдена в базі. Ви успішно авторизовані!"
        keyboard = client_menu(is_authorized=True)

        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                msg = str(e).lower()
                if ("message to edit not found" in msg) or ("message is not modified" in msg):
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

        # Завершуємо сценарій
        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # 2) Якщо картка не знайдена — надсилаємо адміну запит на підтвердження
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
            "Перевірте в базі та натисніть «✅ Підтвердити картку». "
            "Якщо не знайдете цю картку, повідомте клієнту про це окремо."
        ),
        reply_markup=kb
    )

    # 3) Інформуємо користувача, що запит відправлено адміністратору
    confirmation_text = "✅ Ваш запит відправлено адміністратору. Очікуйте підтвердження."
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=confirmation_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e).lower()
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
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

    # Завершуємо сценарій
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

async def cashback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “🎁 Кешбек” в меню авторизованого клієнта.
    Показуємо інформацію про кешбек у тому ж вікні.
    """
    await update.callback_query.answer()
    text = "🎁 Ваш кешбек: 0 UAH (поки що немає активних кешбеків)."
    keyboard = client_menu(is_authorized=True)
    chat_id = update.effective_chat.id

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            msg = str(e).lower()
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
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

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “📖 Історія” в меню авторизованого клієнта.
    Показуємо до 10 останніх операцій (депозитів + виведень).
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id
    from modules.db import get_user_history
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
                lines.append(f"• [Депозит] {amt} UAH ({info}) о {t}")
            else:
                lines.append(f"• [Виведення] {amt} UAH ({info}) о {t}")
        text = "\n".join(lines)

    keyboard = client_menu(is_authorized=True)
    chat_id = update.effective_chat.id

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            msg = str(e).lower()
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
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

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “🔒 Вийти” в меню авторизованого клієнта.
    Видаляємо 'base_msg_id' і повертаємо користувача до неавторизованого меню.
    """
    await update.callback_query.answer()
    chat_id = update.effective_chat.id

    context.user_data.pop("base_msg_id", None)
    text = "🔒 Ви вийшли з профілю. Використовуйте «💳 Мій профіль» для повторної авторизації."
    keyboard = client_menu(is_authorized=False)

    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=keyboard
    )
    context.user_data["base_msg_id"] = sent.message_id

async def help_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “ℹ️ Допомога” в меню авторизованого клієнта.
    Просто показуємо стандартний текст допомоги.
    """
    await update.callback_query.answer()
    text = "ℹ️ Допомога:\n/start — перезапуск бота\n📲 Зверніться до підтримки, якщо є питання."
    keyboard = client_menu(is_authorized=True)
    chat_id = update.effective_chat.id

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=base_id,
                text=text,
                reply_markup=keyboard
            )
        except BadRequest as e:
            msg = str(e).lower()
            if ("message to edit not found" in msg) or ("message is not modified" in msg):
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


# ─── ConversationHandler для “Мій профіль” ─────────────────────────────────────
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
            # Якщо потрібно, сюди можна додати обробку deposit_start та withdraw_start,
            # але вони вже перехоплюються окремими ConversationHandler-ами.
        ]
    },
    fallbacks=[
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler(“Мій профіль”) у групі 0.
    """
    app.add_handler(profile_conv, group=0)
