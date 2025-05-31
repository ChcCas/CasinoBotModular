# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes, Application
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user
from modules.keyboards import client_menu
from modules.callbacks import CB

# ────────────────────────────────────────────────────────────────────────────────
async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор натиснув «✅ Підтвердити картку» (callback_data="admin_confirm_card:user_id:card"):
    1) Авторизуємо користувача (запис у clients).
    2) Повідомляємо користувача: «Картка підтверджена, ви авторизовані».
    3) Оновлюємо повідомлення адміну («Картка … підтверджена»).
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # Додаємо або оновлюємо запис user_id→card
    authorize_card(user_id, card)

    # Повідомляємо клієнта про успішну авторизацію
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # Оновлюємо повідомлення адміну
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )

async def admin_deny_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор натиснув «❌ Картка не знайдена» (callback_data="admin_deny_card:user_id:card"):
    1) Видаляємо callback-повідомлення адміну або оновлюємо текст.
    2) Додаємо user_id у pending_phone (щоб при наступному «Мій профіль» почати введення телефону).
    3) Повідомляємо користувача: «Карта не знайдена, введіть телефон».
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # Оновлюємо текст адміну
    await update.callback_query.message.edit_text(
        f"❌ Для користувача {user_id} картка {card} НЕ знайдена. Запитайте у нього телефон."
    )

    # Додаємо user_id до pending_phone
    from modules.handlers.profile import pending_phone
    pending_phone.add(user_id)

    # Надсилаємо користувачу повідомлення з проханням ввести телефон
    await context.bot.send_message(
        chat_id=user_id,
        text="❗️ Картку не знайдено. Будь ласка, введіть свій номер телефону (0XXXXXXXXX):",
        reply_markup=nav_buttons()
    )

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор натиснув “🛠 Адмін-панель” (callback_data="admin_panel"):
    1) Показуємо клавіатуру admin_panel_kb().
    2) Переходимо в state STEP_ADMIN_SEARCH.
    """
    query = update.callback_query
    await query.answer()
    from modules.keyboards import admin_panel_kb
    await query.message.reply_text("🛠 Адмін-панель:", reply_markup=admin_panel_kb())
    return CB.ADMIN_SEARCH.value  # або відповідний state STEP_ADMIN_SEARCH

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор у полі пошуку вводить ID чи картку.
    Просто заглушка – ви можете реалізувати пошук клієнта (search_user) тут.
    """
    query = update.message.text.strip()
    record = search_user(query)
    if record:
        await update.message.reply_text(f"Найдено: user_id={record['user_id']}, card={record['card']}, phone={record['phone']}")
    else:
        await update.message.reply_text("Користувача не знайдено.")

    return CB.ADMIN_SEARCH.value  # залишаємо адміністратора в цьому state

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Коли адміністратор вводить текст для розсилки.
    Розсилаємо всім клієнтам (використати broadcast_to_all).
    """
    from modules.db import broadcast_to_all
    message = update.message.text
    broadcast_to_all(message)
    await update.message.reply_text("📢 Розсилка надіслана.")
    return CB.ADMIN_BROADCAST.value

def register_admin_handlers(app: Application) -> None:
    """
    Реєструє всі admin-specific хендлери (група 0).
    1) Обробник “🛠 Адмін-панель”
    2) Обробники “admin_confirm_card” та “admin_deny_card”
    3) Обробники пошуку та розсилки (додайте у відповідні group’и чи order’и)
    """
    # Обовʼязково в group=0, щоб ці CallbackQueryHandler спрацювали раніше, ніж загальний роутер.
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(admin_deny_card, pattern=r"^admin_deny_card:\d+:.+"),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
