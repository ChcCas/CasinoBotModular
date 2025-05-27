# src/modules/handlers/admin.py

import re
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from modules.db import (
    list_deposits,
    list_withdrawals,
    list_users,
    search_user,
    broadcast_message,
)
from keyboards import admin_panel_kb, nav_buttons
from modules.states    import (
    STEP_MENU,
    STEP_ADMIN_DEPOSITS,
    STEP_ADMIN_WITHDRAWALS,
    STEP_ADMIN_USERS,
    STEP_ADMIN_STATS,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST,
)

# ——— Адмін-панель ———
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🛠 Адмін-панель",
        reply_markup=admin_panel_kb()
    )
    return STEP_MENU

# ——— Депозити ———
async def admin_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = list_deposits()
    text = "\n".join(f"{r['id']}: {r['user_id']} → {r['amount']}" for r in rows) or "Немає депозитів"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_ADMIN_DEPOSITS

# ——— Виведення ———
async def admin_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = list_withdrawals()
    text = "\n".join(f"{r['id']}: {r['user_id']} → {r['amount']}" for r in rows) or "Немає запитів на виведення"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_ADMIN_WITHDRAWALS

# ——— Користувачі ———
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = list_users()
    text = "\n".join(f"{r['id']}: {r['name']} ({r['phone']})" for r in rows) or "Користувачів не знайдено"
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_ADMIN_USERS

# ——— Статистика ———
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    deps  = len(list_deposits())
    wds   = len(list_withdrawals())
    users = len(list_users())
    text = (
        f"📊 Статистика:\n"
        f"Користувачів: {users}\n"
        f"Депозитів: {deps}\n"
        f"Виведень: {wds}"
    )
    await update.callback_query.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_ADMIN_STATS

# ——— Пошук клієнта ———
async def admin_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть ім’я або частину імені для пошуку:",
        reply_markup=nav_buttons()
    )
    return STEP_ADMIN_SEARCH

async def admin_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    rows = search_user(query)
    if not rows:
        await update.message.reply_text("Користувача не знайдено", reply_markup=nav_buttons())
    else:
        for r in rows:
            await update.message.reply_text(f"{r['id']}: {r['name']} / {r['phone']}", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Розсилка ———
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Введіть текст розсилки:",
        reply_markup=nav_buttons()
    )
    return STEP_ADMIN_BROADCAST

async def admin_broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    count = broadcast_message(text)
    await update.message.reply_text(f"✅ Повідомлення відправлено {count} користувачам", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Реєстрація обробників ———
def register_admin_handlers(app):
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_panel, pattern="^admin_panel$")],
        states={
            STEP_MENU: [
                CallbackQueryHandler(admin_deposits,   pattern="^admin_deposits$"),
                CallbackQueryHandler(admin_withdrawals, pattern="^admin_withdrawals$"),
                CallbackQueryHandler(admin_users,       pattern="^admin_users$"),
                CallbackQueryHandler(admin_stats,       pattern="^admin_stats$"),
                CallbackQueryHandler(admin_search_start,    pattern="^admin_search$"),
                CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"),
            ],
            STEP_ADMIN_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_execute)
            ],
            STEP_ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_execute)
            ],
            # Після перегляду депозитів/виведень/користувачів повертаємося в меню
            STEP_ADMIN_DEPOSITS:    [MessageHandler(filters.ALL, lambda u,c: STEP_MENU)],
            STEP_ADMIN_WITHDRAWALS: [MessageHandler(filters.ALL, lambda u,c: STEP_MENU)],
            STEP_ADMIN_USERS:       [MessageHandler(filters.ALL, lambda u,c: STEP_MENU)],
            STEP_ADMIN_STATS:       [MessageHandler(filters.ALL, lambda u,c: STEP_MENU)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    app.add_handler(conv)
