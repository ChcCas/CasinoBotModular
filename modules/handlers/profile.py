# modules/handlers/profile.py

import re
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME
from keyboards import nav_buttons, client_menu
from states import (
    STEP_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
)

# Если ваш db.py лежит в корне проекта:
from modules.db import get_user, save_user
# Если же в modules/db.py, то:
# from modules.db import get_user, save_user


async def _enter_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Стартовый обработчик по callback_data="client_profile".
    Показывает либо ввод + сохранение, либо сразу профиль.
    """
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)

    if user:
        # Пользователь уже в БД → показываем профиль
        await update.callback_query.message.reply_text(
            f"Ваш профіль:\n\n"
            f"🆔 ID: {user[0]}\n"
            f"💳 Картка: {user[1]}\n"
            f"📞 Телефон: {user[2]}",
            reply_markup=client_menu(authorized=True)
        )
        return STEP_MENU

    # Иначе — просим ввести номер карты
    await update.callback_query.message.reply_text(
        "Будь ласка, введіть номер вашої картки:",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_CARD


async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода номера карты.
    Оставляем только цифры, проверяем длину 4–7.
    """
    text = re.sub(r"\D", "", update.message.text)
    if not (4 <= len(text) <= 7):
        await update.message.reply_text(
            "Невірний формат картки. Має бути від 4 до 7 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_CARD

    context.user_data["profile_card"] = text
    await update.message.reply_text(
        "Дякую! Тепер введіть номер телефону (починається з 0 та має 10 цифр):",
        reply_markup=nav_buttons()
    )
    return STEP_PROFILE_ENTER_PHONE


async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода телефона.
    Оставляем только цифры, проверяем: 10 цифр, начинается с '0'.
    """
    text = re.sub(r"\D", "", update.message.text)
    if not (len(text) == 10 and text.startswith("0")):
        await update.message.reply_text(
            "Невірний формат телефону. Має починатися з 0 + 9 цифр.",
            reply_markup=nav_buttons()
        )
        return STEP_PROFILE_ENTER_PHONE

    context.user_data["profile_phone"] = text

    # Сохраняем в БД
    save_user(
        update.effective_user.id,
        context.user_data["profile_card"],
        context.user_data["profile_phone"]
    )

    # Отправляем подтверждение и показываем профиль
    await update.message.reply_text(
        "Ви успішно авторизовані! Ось ваш профіль:",
        reply_markup=client_menu(authorized=True)
    )
    return STEP_MENU


async def profile_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка кнопки 🔓 Вийти — сброс авторизации для текущей сессии.
    """
    await update.callback_query.answer()
    # Удаляем временные данные — при следующем нажатии / «Мій профіль» снова попросим ввести
    context.user_data.pop("profile_card", None)
    context.user_data.pop("profile_phone", None)

    await update.callback_query.message.reply_text(
        "Ви вийшли з профілю.",
        reply_markup=client_menu(authorized=False)
    )
    return STEP_MENU


def register_profile_handlers(app):
    """
    Регистрируем все хендлеры сценария «Мій профіль».
    """
    # 1) По нажатию кнопки «Мій профіль»
    app.add_handler(
        CallbackQueryHandler(_enter_profile, pattern="^client_profile$"),
        group=0
    )

    # 2) Ввод карты и телефона (только по текстовым сообщениям, не командам)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card),
        group=1
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone),
        group=1
    )

    # 3) Выход из профиля
    app.add_handler(
        CallbackQueryHandler(profile_exit, pattern="^logout$"),
        group=2
    )
