# modules/handlers/profile.py
import re
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID
from db               import get_user, upsert_user
from keyboards        import nav_buttons, client_menu
from states           import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
)

def register_profile_handlers(app):
    # «Мій профіль»
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0
    )
    # введення картки
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1
    )
    # введення телефону
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=1
    )
    # введення SMS-коду
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_code),
        group=1
    )

async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перша точка входу в профіль."""
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    if user:
        # вже авторизований
        await query.message.reply_text(
            "Ви вже авторизовані!",
            reply_markup=client_menu(authorized=True)
        )
        return STEP_MENU

    # новий користувач → просимо картку
    await query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD

async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = re.sub(r"\D", "", update.message.text)  # лиш цифри
    if not (4 <= len(text) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["profile_card"] = text
    await update.message.reply_text(
        "Дякую! Тепер введіть номер телефону (починається з 0, 10 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE

async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = re.sub(r"\D", "", update.message.text)
    if not (phone.startswith("0") and len(phone) == 10):
        await update.message.reply_text(
            "Невірний формат телефону. Має починатися з 0 і бути 10 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    context.user_data["profile_phone"] = phone

    # повідомити адміністратору
    name = update.effective_user.full_name
    await context.bot.send_message(
        ADMIN_ID,
        f"Запит на авторизацію від {name} ({update.effective_user.id}):\n"
        f"Картка: {context.user_data['profile_card']}\n"
        f"Телефон: {phone}\n\n"
        "Відправте клієнту 4-значний код."
    )

    await update.message.reply_text(
        "Код надіслано адміністратору. Введіть 4-значний код:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CODE

async def profile_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = re.sub(r"\D", "", update.message.text)
    if len(code) != 4:
        await update.message.reply_text(
            "Невірний код. Має бути 4 цифри.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CODE

    # адміну – отриманий код
    name = update.effective_user.full_name
    await context.bot.send_message(
        ADMIN_ID,
        f"Код від {name} ({update.effective_user.id}): {code}"
    )

    # зберегти в БД
    upsert_user(
        update.effective_user.id,
        context.user_data["profile_card"],
        context.user_data["profile_phone"]
    )

    # очистити тимчасові
    context.user_data.pop("profile_card", None)
    context.user_data.pop("profile_phone", None)

    await update.message.reply_text(
        "Ви успішно авторизовані!",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU
