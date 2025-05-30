from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from modules.keyboards import admin_panel_kb
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, Application
from modules.db import authorize_card
from modules.keyboards import client_menu
from modules.callbacks import CB

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # callback_data = "admin_confirm_card:<user_id>:<card>"
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)
    # 1) Зберігаємо в БД
    authorize_card(user_id, card)
    # 2) Повідомляємо клієнта
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )
    # 3) Оновлюємо повідомлення адміну
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )

def register_admin_handlers(app: Application) -> None:
    # Вставте перед іншими CallbackQueryHandler
    app.add_handler(
        CallbackQueryHandler(
            admin_confirm_card,
            pattern=r"^admin_confirm_card:\d+:.+"
        ),
        group=0
    )
    # Далі існуючі реєстрації:
    # register other handlers...
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
