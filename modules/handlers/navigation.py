# modules/handlers/navigation.py

import sqlite3
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from modules.callbacks import CB
from modules.keyboards import (
    nav_buttons, main_menu, admin_panel_kb
)
from modules.states import (
    STEP_MENU,
    STEP_DEPOSIT_AMOUNT,
    STEP_WITHDRAW_AMOUNT,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)
from .start import start_command
from .admin import show_admin_panel

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Універсальний роутер для всіх callback_query, які не перехоплені ConversationHandler-ами групи 0.
    Якщо нічого не знайдено — повертаємося до start_command (STEP_MENU).
    """
    query = update.callback_query
    data = query.data
    await query.answer()

    # ─── Адмін-панель ───
    if data == "admin_panel":
        return await show_admin_panel(update, context)

    # ─── «Головне меню» або «◀️ Назад» ───
    if data in (CB.HOME.value, CB.BACK.value):
        return await start_command(update, context)

    # ─── Депозит ───
    if data == CB.DEPOSIT_START.value:
        await query.message.reply_text(
            "💸 Введіть суму для поповнення:", reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    # ─── Виведення ───
    if data == CB.WITHDRAW_START.value:
        await query.message.reply_text(
            "💳 Введіть суму для виведення:", reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    # ─── Допомога ───
    if data == CB.HELP.value:
        await query.message.reply_text(
            "ℹ️ Допомога:\n/start — перезапуск бота\n📲 Зверніться до підтримки, якщо є питання.",
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    # ─── Адмін: Пошук клієнта ───
    if data == CB.ADMIN_SEARCH.value:
        await query.message.reply_text(
            "🔍 Введіть ID або картку для пошуку:", reply_markup=nav_buttons()
        )
        return STEP_ADMIN_SEARCH

    # ─── Адмін: Розсилка ───
    if data == CB.ADMIN_BROADCAST.value:
        await query.message.reply_text(
            "📢 Введіть текст для розсилки:", reply_markup=nav_buttons()
        )
        return STEP_ADMIN_BROADCAST

    # ─── Якщо нічого не спрацювало ───
    return await start_command(update, context)

def register_navigation_handlers(app: Application):
    """
    Реєструємо:
      1) CallbackQueryHandler(start_command, pattern="^home$")
      2) CallbackQueryHandler(start_command, pattern="^back$")
      3) CallbackQueryHandler(menu_handler, pattern=".*")
    У групі 1, щоб усі CALLBACK, які не потрапили в ConversationHandler- group=0, оброблялися тут.
    """
    # 1) Якщо натиснули «Головне меню» / «Назад»
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^home$"),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(start_command, pattern="^back$"),
        group=1
    )

    # 2) Все інше — menu_handler
    app.add_handler(
        CallbackQueryHandler(menu_handler, pattern=".*"),
        group=1
    )
