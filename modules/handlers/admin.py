from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.keyboards import admin_panel_kb, client_menu
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from modules.db import authorize_card, search_user, broadcast_to_all

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🛠 Адмін-панель:", reply_markup=admin_panel_kb())
    return STEP_ADMIN_SEARCH

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник кнопки “admin_confirm_card:<user_id>:<card>” 
    у повідомленні, яке адміністратор отримав від клієнта.
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо у clients
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена адміністратором. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Оновлюємо повідомлення адміну
    await update.callback_query.message.edit_text(f"✅ Картка {card} для користувача {user_id} підтверджена.")
    return STEP_MENU

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Тут просто просимо ввести ID або картку для пошуку:
    await update.message.reply_text("🔍 Введіть ID або картку для пошуку:")
    return STEP_ADMIN_BROADCAST

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    broadcast_to_all(text)
    await update.message.reply_text("📢 Розсилка запущена.")
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    # 1) Спершу — опрацювання підтвердження картки (має пріоритет, group=0)
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+",),
        group=0
    )

    # 2) Потім – кнопка «admin_panel»
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )

    # 3) Оброблювачі введення тексту в адмінській частині
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search),
        group=1
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=1
    )
