from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from modules.keyboards import admin_panel_kb
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🛠 Адмін-панель:", reply_markup=admin_panel_kb())
    return STEP_ADMIN_SEARCH

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Введіть ID або картку для пошуку:")
    return STEP_ADMIN_BROADCAST

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # тут логіка розсилки …
    await update.message.reply_text("📢 Розсилка запущена.")
    return STEP_MENU

def register_admin_handlers(app):
    app.add_handler(CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search),   group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast), group=1)
