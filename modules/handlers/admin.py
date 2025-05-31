# modules/handlers/admin.py

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.keyboards import admin_panel_kb, client_menu
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from modules.db import authorize_card, find_user, broadcast_to_all

# ─── 1) Кнопка “✅ Підтвердити картку” (callback_data = "admin_confirm_card:<user_id>:<card>") ───
async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # callback_data формат: "admin_confirm_card:<user_id>:<card>"
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо картку у вашій БД (authorize_card – функція у modules/db.py)
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта, що картка підтверджена
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Редагуємо повідомлення адміну, щоби воно відобразило статус
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )

# ─── 2) Показ адмін-панелі (кнопка “🛠 Адмін-панель”) ───
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🛠 Адмін-панель:", 
        reply_markup=admin_panel_kb()
    )
    return STEP_ADMIN_SEARCH

# ─── 3) Сценарій пошуку клієнта (STEP_ADMIN_SEARCH) ───
async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор натиснув «🔍 Пошук клієнта».
    Запитуємо ID або номер картки, потім маємо окремий обробник знаходження.
    """
    if update.callback_query:
        await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🔍 Введіть ID або номер картки для пошуку клієнта:",
        reply_markup=nav_buttons()
    )
    return STEP_ADMIN_BROADCAST

# ─── 4) Сценарій розсилки (STEP_ADMIN_BROADCAST) ───
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор вводить текст після «Розсилка»,
    ми надсилаємо його всім користувачам (функція broadcast_to_all у modules/db.py).
    """
    text = update.message.text
    # Припустимо, що у вас є функція broadcast_to_all(text),
    # яка розсилає текст всім користувачам БД.
    broadcast_to_all(text)
    await update.message.reply_text("📢 Розсилка успішно виконана.", reply_markup=nav_buttons())
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    """
    Реєструє усі адмінські CallbackQueryHandler та MessageHandler:
     1) admin_confirm_card (підтвердження картки)
     2) show_admin_panel (натискання «🛠 Адмін-панель»)
     3) admin_search (початок пошуку, callback_data="admin_search")
     4) admin_broadcast (текст від адміна для розсилки)
    """
    # 1) Підтвердження картки клієнта
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )

    # 2) Кнопка «🛠 Адмін-панель»
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern=f"^{CB.ADMIN_PANEL.value}$"),
        group=0
    )

    # 3) Пошук клієнта: спочатку ловимо callback_data="admin_search"
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    # Потім, коли адміністратор вводить текст (ID чи картку), ловимо будь-який текст у цьому стані
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )

    # 4) Розсилка: спочатку ловимо callback_data="admin_broadcast"
    app.add_handler(
        CallbackQueryHandler(lambda u, c: c, pattern=f"^{CB.ADMIN_BROADCAST.value}$"),
        group=0
    )
    # Фактичний текст для розсилки: MessageHandler filters.TEXT
    # (суто для прикладу, можна винести в окремий ConversationHandler)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
