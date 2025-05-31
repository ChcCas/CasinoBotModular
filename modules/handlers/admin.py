# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user, broadcast_to_all
from modules.keyboards import client_menu, nav_buttons, admin_panel_kb
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє callback_data = "admin_confirm_card:<user_id>:<card>".
    1) Зберігає картку у базі через authorize_card(...)
    2) Повідомляє клієнта, що його картка підтверджена, та показує client_menu(is_authorized=True)
    3) Редагує оригінальне повідомлення адміну, підтверджуючи операцію.
    """
    await update.callback_query.answer()
    # callback_data формату "admin_confirm_card:12345:4000123412341234"
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо картку у таблиці clients
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Редагуємо повідомлення адміну
    try:
        await update.callback_query.message.edit_text(
            text=f"✅ Картка {card} для користувача {user_id} підтверджена."
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise

    return

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Відображає головне повідомлення адмін-панелі з клавіатурою admin_panel_kb.
    """
    await update.callback_query.answer()
    text = "🛠 Адмін-панель:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=admin_panel_kb()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_ADMIN_SEARCH

# ... (інші адмінські хендлери: admin_search, admin_search_result, admin_broadcast) ...

def register_admin_handlers(app: Application) -> None:
    """
    Додає всі CallbackQueryHandler та MessageHandler для адмінського функціоналу:
      1) Підтвердження картки клієнта (admin_confirm_card)
      2) Відображення адмін-панелі (show_admin_panel)
      3) Пошук клієнта (admin_search + admin_search_result)
      4) Розсилка (admin_broadcast)
    """
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )
    # ... реєстрація інших адмінських хендлерів (admin_search, admin_search_result, admin_broadcast) ...
