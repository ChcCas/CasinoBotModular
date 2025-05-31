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
from modules.states import STEP_FIND_CARD_PHONE, STEP_MENU, STEP_ENTER_PHONE, STEP_ENTER_CODE

# ────────────────────────────────────────────────────────────────────────────────
# Глобальні структури для «чекання» введення телефону та коду користувачем
pending_phone = set()     # містить user_id, які зараз очікують ввести телефон
pending_code  = set()     # містить user_id, які зараз очікують ввести код підтвердження
# ────────────────────────────────────────────────────────────────────────────────

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли користувач натиснув “💳 Мій профіль” (callback_data="client_profile"):
    1) Якщо у clients є запис user_id→card → показуємо меню авторизованого клієнта.
    2) Якщо картки нема → просимо ввести картку.
    3) Якщо user_id в pending_phone → просимо ввести телефон.
    4) Якщо user_id в pending_code → просимо ввести код.
    """
    await update.callback_query.answer()
    user_id = update.effective_user.id

    # Якщо зараз очікуємо від нього вводити телефон
    if user_id in pending_phone:
        prompt = "📞 Будь ласка, введіть свій номер телефону (0XXXXXXXXX):"
        sent = await update.callback_query.message.reply_text(prompt, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id
        return STEP_ENTER_PHONE

    # Якщо зараз очікуємо від нього вводити код
    if user_id in pending_code:
        prompt = "🔑 Введіть код підтвердження, який ви отримали:"
        sent = await update.callback_query.message.reply_text(prompt, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id
        return STEP_ENTER_CODE

    # Перевіряємо: чи є вже в базі (user_id → card)?
    user_record = search_user(str(user_id))
    if user_record and user_record.get("card"):
        # Авторизований користувач → показуємо меню авторизованого
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
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.callback_query.message.reply_text(text, reply_markup=keyboard)
            context.user_data["base_msg_id"] = sent.message_id

        return STEP_MENU

    # Якщо ще не було авторизації → запитуємо картку
    prompt = "💳 Введіть номер вашої клубної картки:"
    sent = await update.callback_query.message.reply_text(prompt, reply_markup=nav_buttons())
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_FIND_CARD_PHONE


async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли користувач вводить картку:
    1) Якщо картка є у БД (search_user) → authorize_card(user_id, card) → показуємо меню авторизованого.
    2) Якщо картки немає → надсилаємо адміну повідомлення з двома кнопками:
         • ✅ Підтвердити картку
         • ❌ Картка не знайдена
       і повідомлення користувачу “Запит на перевірку надіслано адміністратору.”
    3) Завершуємо ConversationHandler.END.
    """
    card = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # 1) Перевіряємо, чи картка вже є в базі
    existing = search_user(card)
    if existing:
        # Якщо адміністратор раніше вже додав таку картку → авторизовуємо користувача
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
                    sent = await update.message.reply_text(text, reply_markup=keyboard)
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        else:
            sent = await update.message.reply_text(text, reply_markup=keyboard)
            context.user_data["base_msg_id"] = sent.message_id

        # Завершуємо (ConversationHandler.END) та очищаємо базове повідомлення
        context.user_data.pop("base_msg_id", None)
        return ConversationHandler.END

    # 2) Якщо картки немає → надсилаємо адміну запит і даємо дві кнопки
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Підтвердити картку",
                callback_data=f"admin_confirm_card:{user_id}:{card}"
            ),
            InlineKeyboardButton(
                "❌ Картка не знайдена",
                callback_data=f"admin_deny_card:{user_id}:{card}"
            ),
        ]
    ])
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"ℹ️ Користувач {full_name} (ID {user_id})\n"
            f"ввів картку: {card}\n"
            "Перевірте в базі. Якщо знайдена — натисніть «✅ Підтвердити картку»,\n"
            "якщо картки не знайдено — натисніть «❌ Картка не знайдена». "
        ),
        reply_markup=kb
    )

    # Інформуємо користувача, що запит надіслано адміну
    confirmation_text = "✅ Ваш запит на перевірку картки відправлено адміністратору. Очікуйте результат."
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
                sent = await update.message.reply_text(confirmation_text, reply_markup=nav_buttons())
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.message.reply_text(confirmation_text, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id

    context.user_data.pop("base_msg_id", None)
    return ConversationHandler.END


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє повідомлення з телефонним номером:
    1) Перевіряємо формат (0XXXXXXXXX). Якщо невірно — повторюємо запит STEP_ENTER_PHONE.
    2) Надсилаємо адміну:
         "Користувач X (ID) надав номер телефону: +380XXXXXXXXX".
       Інформуємо користувача: "На ваш номер надіслано код підтвердження. Введіть його."
    3) Додаємо user_id у pending_code, видаляємо з pending_phone, переводимо в STEP_ENTER_CODE.
    """
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    # Перевіряємо формат: мусить починатися з '0' і 10 цифр
    import re
    if not re.fullmatch(r"^0\d{9}$", phone):
        error_text = "❗️ Невірний формат. Номер має вигляд 0XXXXXXXXX. Спробуйте ще раз:"
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=error_text,
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.message.reply_text(error_text, reply_markup=nav_buttons())
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        return STEP_ENTER_PHONE

    # 1) Надсилаємо адміну повідомлення з телефоном
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"ℹ️ Користувач {full_name} (ID {user_id}) надав номер телефону: {phone}\n"
            "Будь ласка, відправте йому код підтвердження поза ботом, "
            "після чого користувач введе цей код у чаті."
        )
    )

    # 2) Інформуємо користувача
    user_text = "✅ На ваш номер надіслано код підтвердження. Будь ласка, введіть його:"
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=user_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.message.reply_text(user_text, reply_markup=nav_buttons())
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.message.reply_text(user_text, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id

    # 3) Переміщаємо user_id з pending_phone → pending_code
    pending_phone.discard(user_id)
    pending_code.add(user_id)

    return STEP_ENTER_CODE


async def enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє код, який ввів користувач:
    1) Перевіряємо, що це 4 цифри; якщо ні — залишаємося в STEP_ENTER_CODE.
    2) Пересилаємо адміну:
         "Користувач X (ID) ввів код: 1234".
    3) Повідомляємо користувача: "Очікуйте, ми знайдемо вашу картку і надішлемо."
    4) Очищаємо pending_code та завершуємо.
    """
    code = update.message.text.strip()
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name

    import re
    if not re.fullmatch(r"^\d{4}$", code):
        error_text = "❗️ Код повинен містити 4 цифри. Спробуйте ще раз:"
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=error_text,
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.message.reply_text(error_text, reply_markup=nav_buttons())
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        return STEP_ENTER_CODE

    # 1) Надсилаємо адміну код
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"ℹ️ Користувач {full_name} (ID {user_id}) ввів код підтвердження: {code}"
    )

    # 2) Повідомляємо користувача, що далі адміністрація знайде картку
    user_text = "ℹ️ Ми отримали ваш код підтвердження. Очікуйте, адміністрація знайде вашу картку і надішле її вам."
    base_id = context.user_data.get("base_msg_id")
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=user_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.message.reply_text(user_text, reply_markup=nav_buttons())
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    else:
        sent = await update.message.reply_text(user_text, reply_markup=nav_buttons())
        context.user_data["base_msg_id"] = sent.message_id

    # 3) Очищаємо pending_code
    pending_code.discard(user_id)
    return ConversationHandler.END


# ─── ConversationHandler для “Мій профіль” ────────────────────────────────────
profile_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_profile, pattern=f"^{CB.CLIENT_PROFILE.value}$")
    ],
    states={
        STEP_FIND_CARD_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)
        ],
        STEP_ENTER_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)
        ],
        STEP_ENTER_CODE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code)
        ],
        STEP_MENU: [
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CB.HOME.value}$"),
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
    Регіструє ConversationHandler для “Мій профіль” (група 0),
    щоб обробляти введення картки, телефону та коду.
    """
    app.add_handler(profile_conv, group=0)
