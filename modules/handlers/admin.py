from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user, broadcast_to_all
from modules.keyboards import admin_panel_kb, client_menu
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник натискання “🛠 Адмін-панель” (callback_data="admin_panel").
    Показуємо клавіатуру адмін-панелі.
    """
    query = update.callback_query
    await query.answer()
    sent = await query.message.reply_text(
        "🛠 Адмін-панель:",
        reply_markup=admin_panel_kb()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_ADMIN_SEARCH

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник у адмін-панелі: коли адмін натиснув “🔍 Пошук клієнта”.
    Запитуємо, щоб адміністратор ввів ID чи картку для пошуку.
    """
    await update.callback_query.message.reply_text(
        "🔍 Введіть ID або номер картки для пошуку:",
        reply_markup=client_menu(is_authorized=False)
    )
    return STEP_ADMIN_BROADCAST  # далі адмін надсилає текст або картку, яку шукаємо

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник у адмін-панелі: коли адмін натиснув “📢 Розсилка”.
    Відправляємо адміністратору запит ввести текст повідомлення для broadcast.
    """
    await update.message.reply_text(
        "📢 Введіть текст, який потрібно розіслати всім користувачам:",
        reply_markup=client_menu(is_authorized=False)
    )
    return STEP_MENU

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник callback_data рівного r"^admin_confirm_card:\d+:.+$".
    Розбирає callback_data = "admin_confirm_card:<user_id>:<card>".
    Зберігає картку в БД (authorize_card), повідомляє користувача.
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # Зберігаємо в БД (authorize_card) — потрібно, щоби потім користувач зміг увійти тим же card
    authorize_card(user_id, card)

    # Повідомляємо клієнта
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            f"🎉 Ваша картка {card} підтверджена адміністратором.\n"
            "Ви тепер успішно авторизовані. Використайте «💳 Мій профіль» ще раз."
        ),
        reply_markup=client_menu(is_authorized=True)
    )

    # Оновлюємо повідомлення адміну, щоби він бачив, що картка підтверджена
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )

def register_admin_handlers(app: Application) -> None:
    """
    Регіструє всі callback і message-хендлери для адмін-панелі (група=0).
    """
    # 1) Обробник «Адмін-панель»
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )
    # 2) Обробник при натисканні «✅ Підтвердити картку»
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+$"),
        group=0
    )
    # 3) Інші адмінські сценарії (пошук, розсилка тощо):
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
