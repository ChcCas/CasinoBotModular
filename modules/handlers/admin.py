# src/modules/handlers/admin.py

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from keyboards import admin_panel_kb, nav_buttons, main_menu
from states    import (
    STEP_ADMIN_BROADCAST,
    STEP_ADMIN_SEARCH,
    STEP_MENU,
)
from modules.db import (
    get_all_users,
    get_all_deposits,
    get_all_withdrawals,
    search_user_by_id,
    broadcast_message,
)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Головне вікно адмін-панелі"""
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "👮 Адмін-панель",
        reply_markup=admin_panel_kb()
    )
    return STEP_MENU


async def show_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    deposits = get_all_deposits()
    text = "\n".join(f"{d.id}: {d.user_id} → {d.amount}" for d in deposits) or "Немає депозитів"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_MENU


async def show_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    withdraws = get_all_withdrawals()
    text = "\n".join(f"{w.id}: {w.user_id} → {w.amount}" for w in withdraws) or "Немає запитів на виведення"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_MENU


async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    users = get_all_users()
    text = "\n".join(f"{u.id}: {u.card} / {u.phone}" for u in users) or "Немає користувачів"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_MENU


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    users = len(get_all_users())
    deposits = sum(d.amount for d in get_all_deposits())
    withdraws = sum(w.amount for w in get_all_withdrawals())
    text = (
        f"📊 Статистика:\n"
        f"Користувачів: {users}\n"
        f"Суми депозитів: {deposits}\n"
        f"Суми виведень: {withdraws}"
    )
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_MENU


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть ID користувача для пошуку:",
        reply_markup=nav_buttons(),
    )
    return STEP_ADMIN_SEARCH


async def do_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = re.sub(r"\D", "", update.message.text)
    result = search_user_by_id(int(user_id) if user_id else None)
    if not result:
        await update.message.reply_text("Користувача не знайдено.", reply_markup=nav_buttons())
    else:
        await update.message.reply_text(
            f"ID: {result.id}\nКартка: {result.card}\nТелефон: {result.phone}",
            reply_markup=nav_buttons()
        )
    return STEP_MENU


async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть текст розсилки:",
        reply_markup=nav_buttons(),
    )
    return STEP_ADMIN_BROADCAST


async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    count = broadcast_message(text)
    await update.message.reply_text(f"Розсилка відправлена {count} користувачам.", reply_markup=nav_buttons())
    return STEP_MENU


def register_admin_handlers(app):
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_panel, pattern="^admin_panel$")],
        states={
            STEP_MENU: [
                CallbackQueryHandler(show_deposits,        pattern="^admin_deposits$"),
                CallbackQueryHandler(show_users,           pattern="^admin_users$"),
                CallbackQueryHandler(show_withdrawals,     pattern="^admin_withdrawals$"),
                CallbackQueryHandler(stats,                pattern="^admin_stats$"),
                CallbackQueryHandler(start_search,         pattern="^admin_search$"),
                CallbackQueryHandler(start_broadcast,      pattern="^admin_broadcast$"),
            ],
            STEP_ADMIN_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, do_search)
            ],
            STEP_ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(conv)
