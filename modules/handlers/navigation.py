# modules/handlers/navigation.py

import sqlite3
import re
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from modules.config import DB_NAME
from modules.callbacks import CB
from modules.keyboards import (
    nav_buttons,
)
from modules.states import (
    STEP_MENU,
    STEP_DEPOSIT_AMOUNT,
    STEP_WITHDRAW_AMOUNT,
    STEP_REG_NAME,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)
from .start import start_command
from .admin import show_admin_panel

def _init_threads():
    """Створює таблицю threads, якщо потрібна (поки можна залишити, але наразі не використовується)."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            user_id INTEGER PRIMARY KEY,
            base_msg_id INTEGER
        )
        """)
        conn.commit()

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Загальний роутер для всіх callback_query, які не були спіймані ConversationHandler-ами.
    Ловить усі callback_data, крім тих, що обробляються у profile_conv, deposit_conv, withdraw_conv, admin_conv.
    Залежно від CB.* викликає відповідну логіку.
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── Повернення “Головне меню” чи “Назад” ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── Початок депозиту ───
    if data == CB.DEPOSIT_START.value:
        # Тут ми передаємо контроль до deposit_conv
        return

    # ─── Початок виведення ───
    if data == CB.WITHDRAW_START.value:
        # Тут ми передаємо контроль до withdraw_conv
        return

    # ─── Реєстрація (якщо вам потрібен окремий сценарій) ───
    if data == "register":
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="📝 Введіть ваше ім’я:",
                reply_markup=nav_buttons()
            )
        # Повернення стану STEP_REG_NAME (якщо потрібен сценарій реєстрації)
        return STEP_REG_NAME

    # ─── Допомога ───
    if data == CB.HELP.value:
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
                reply_markup=nav_buttons()
            )
        return STEP_MENU

    # ─── Адмін: пошук користувача ───
    if data == CB.ADMIN_SEARCH.value:
        return await show_admin_panel(update, context)

    # ─── Адмін: розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        return

    # Якщо callback_data жодна з наведених вище — повертаємося у головне меню
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    """
    Додаємо:
     1) Усі ConversationHandler-и (profile_conv, deposit_conv, withdraw_conv, admin_conv) реєструються у групі 0.
     2) Тільки потім реєструємо загальні CallbackQueryHandler ↓ (група 1),
        які ловлять усі інші callback_query (.*).
    """
    _init_threads()

    # Обробка кнопок “Головне меню” чи “Назад” — одразу викликають start_command
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"), group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"), group=1
    )

    # Основний роутер для всіх непопадань в інші ConversationHandler-и
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"), group=1
    )
