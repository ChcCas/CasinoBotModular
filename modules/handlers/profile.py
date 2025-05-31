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
from modules.db import authorize_card, search_user, get_user_history
from modules.keyboards import nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач натиснув “💳 Мій профіль” (callback_data="client_profile").
    1) Якщо у clients є запис для цього user_id з полем card → показуємо меню авторизованого користувача.
    2) Якщо нема картки → запитуємо “💳 Введіть номер картки:”.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id

    # Перевіряємо в БД
    user_record = search_user(str(user_id))
    if user_record and user_record.get("card"):
        # Користувач уже авторизований: показуємо меню авторизованого
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
                # Прагнемо редагувати наявне повідомлення
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=text,
                    reply_markup=keyboard
                )
            except BadRequest as e:
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    # Якщо base_msg видалено або текст не змінився → надсилаємо нове повідомлення
                    sent = await update.callback_query.message.reply_text(
                        text,
                        reply_markup=keyboard
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            # Якщо ще не було base_msg → надсилаємо нове
            sent = await update.callback_query.message.reply_text(
                text,
                reply_markup=keyboard
            )
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо користувача нема в БД або нема картки → запитуємо номер картки
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
    1) Перевіряємо, чи існує така картка у БД (search_user(card)):
       - Якщо є → “авторизуємо” (authorize_card), показуємо меню авторизованого.
       - Якщо нема → надсилаємо адміну запит “admin_confirm_card:<user_id>:<card>”.
    2) Редагуємо (або надсилаємо нове) повідомлення клієнту:
       - Якщо авторизовані → “Картку знайдено…”
       - Якщо не знайдено → “Ваш запит відправлено адміністратору…”
    3) Завершуємо сценарій (ConversationHandler.END).
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # 1) Перевірка: чи вже є така картка у БД?
    existing = search_user(card)
    if existing:
        # — Якщо картка знайдена (ймовірно, адміністратор підтвердив раніше)
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

        # Завершуємо
        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # 2) Якщо картки немає — надсилаємо адміну кнопку для підтвердження
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

    # 3) Інформуємо клієнта, що запит відправлено адміністратору
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

    # Завершуємо та очищаємо base_msg_id
    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END

# ─── Додаткові обробники для кнопок у меню авторизованого користувача ───

async def cashback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “🎁 Кешбек” в меню авторизованого користувача.
    Просто надсилаємо інформацію (можна розширити бізнес-логіку).
    """
    await update.callback_query.answer()
    text = "🎁 Ваш кешбек: 0 UAH (поки що немає активних кешбеків)."
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=text,
                reply_markup=client_menu(is_authorized=True)
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.callback_query.message.reply_text(
                    text,
                    reply_markup=client_menu(is_authorized=True)
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.callback_query.message.reply_text(
            text,
            reply_markup=client_menu(is_authorized=True)
        )
        context.user_data["base_msg_id"] = sent.message_id

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “📖 Історія” в меню авторизованого користувача.
    Виводить до 10 останніх транзакцій (депозитів + виведень).
    """
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
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
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
    Обробник для кнопки “🔒 Вийти” в меню авторизованого користувача.
    Просто видаляємо 'base_msg_id' (щоб при наступному вході в меню знову запитати картку)
    і повертаємо клієнта в головне меню (як неавторизованого).
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id

    # Якщо хочемо — можна також видалити картку з БД, але зазвичай "logout" 
    # означає просто скидання сесії, не обов’язково видаляти запис у clients.
    # Тому просто очищуємо base_msg_id, а головне меню покаже, що користувач 
    # більше не авторизований.
    context.user_data.pop("base_msg_id", None)

    text = "🔒 Ви вийшли з профілю. Використовуйте “💳 Мій профіль” для повторної авторизації."
    keyboard = client_menu(is_authorized=False)

    # Надсилаємо або редагуємо повідомлення
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=keyboard
    )
    context.user_data["base_msg_id"] = sent.message_id

async def help_auth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник для кнопки “ℹ️ Допомога” у меню авторизованого користувача.
    Просто показуємо стандартний текст допомоги.
    """
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
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
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

# ─── ConversationHandler для сценарію “Мій профіль” ────────────────────────────
profile_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
        # Після того, як користувач у “STEP_MENU” (тобто вже авторизований), 
        # ми обробляємо натискання на кнопки в меню авторизованого клієнта.
        STEP_MENU: [
            CallbackQueryHandler(cashback_handler, pattern=r"^cashback$"),
            CallbackQueryHandler(history_handler, pattern=r"^history$"),
            CallbackQueryHandler(logout_handler, pattern=r"^logout$"),
            CallbackQueryHandler(help_auth_handler, pattern=f"^{CB.HELP.value}$"),
            # Кнопки “deposit_start” та “withdraw_start” будуть оброблені окремими ConversationHandler-ами
        ]
    },
    fallbacks=[
        # Якщо користувач натисне “Назад”/“Головне меню” — просто виходимо з цього сценарію
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
        CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
    ],
    per_chat=True,
)

def register_profile_handlers(app: Application) -> None:
    """
    Регіструє ConversationHandler для “Мій профіль” (група 0),
    щоб усі callback_data, які починаються з “client_profile” або
    з меню авторизованого клієнта, оброблялися до загального навігаційного.
    """
    app.add_handler(profile_conv, group=0)
