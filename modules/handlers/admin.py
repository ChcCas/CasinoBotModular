# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.keyboards import admin_panel_kb, client_menu, nav_buttons
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from modules.db import authorize_card, search_user, broadcast_to_all

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    CallbackQueryHandler для “admin_confirm_card:<user_id>:<card>”.
    Адмін натиснув “Підтвердити картку”.
    1) Зберігаємо картку у таблицю clients.
    2) Повідомляємо клієнта про успіх (та показуємо клієнтське меню із is_authorized=True).
    3) Оновлюємо повідомлення адміну, що операція успішна.
    """
    await update.callback_query.answer()

    # Розбираємо callback_data
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо в БД
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта, що його картку підтверджено
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Оновлюємо повідомлення адміну
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )
    return

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    CallbackQueryHandler для “admin_panel” (натискання “🛠 Адмін-панель”).
    Відображаємо адмін-панель.
    """
    await update.callback_query.answer()

    text = "🛠 Адмін-панель:"
    sent = await update.callback_query.message.reply_text(
        text,
        reply_markup=admin_panel_kb()
    )
    context.user_data["base_msg_id"] = sent.message_id
    return STEP_ADMIN_SEARCH

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    CallbackQueryHandler для “admin_search” (натискання “🔍 Пошук клієнта”).
    Запитуємо ID або картку. Використовуємо те саме повідомлення (редагуємо).
    """
    await update.callback_query.answer()

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="🔍 Введіть ID або номер картки для пошуку:",
            reply_markup=nav_buttons()
        )
    return STEP_ADMIN_BROADCAST  # далі ловиться як MessageHandler

async def admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    MessageHandler, який спрацьовує після того, як адмiн ввів ID/номер картки.
    Використовуємо search_user(query) для пошуку.
    Потім редагуємо те саме повідомлення, показуючи результат.
    """
    query = update.message.text.strip()
    user = search_user(query)

    if user:
        text = (
            f"👤 Знайдено клієнта:\n"
            f"• user_id: {user['user_id']}\n"
            f"• card: {user['card']}\n"
            f"• phone: {user['phone'] or 'Не вказано'}"
        )
    else:
        text = "❌ Клієнта з таким ID або карткою не знайдено."

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text=text,
            reply_markup=nav_buttons()
        )
    return STEP_MENU

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Якщо CallbackQuery (кнопка “📢 Розсилка”), то просимо ввести текст.
    2) Якщо Message (адмін ввів текст), виконуємо broadcast_to_all і повертаємось до меню.
    """
    # Якщо це був CallbackQueryHandler (натискання “📢 Розсилка”)
    if update.callback_query:
        await update.callback_query.answer()
        base_id = context.user_data.get("base_msg_id")
        if base_id:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text="📢 Введіть текст для розсилки всім клієнтам:",
                reply_markup=nav_buttons()
            )
        return STEP_ADMIN_BROADCAST

    # Якщо це MessageHandler (адмін вводить текст для розсилки)
    text_to_send = update.message.text.strip()
    broadcast_to_all(text_to_send)

    base_id = context.user_data.get("base_msg_id")
    if base_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=base_id,
            text="✅ Розсилка успішно надіслана всім клієнтам.",
            reply_markup=nav_buttons()
        )
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    """
    Регіструємо всі адмінські хендлери (у групі 0):
     1) admin_confirm_card
     2) show_admin_panel
     3) admin_search
     4) admin_search_result
     5) admin_broadcast (і через CallbackQueryHandler, і через MessageHandler)
    """
    # 1) Підтвердження картки клієнта (натискання “✅ Підтвердити картку”)
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )

    # 2) Кнопка “🛠 Адмін-панель”
    from modules.callbacks import CB
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern=f"^admin_panel$"),
        group=0
    )

    # 3) “🔍 Пошук клієнта” (CallbackQuery → потім адмін вводить текст)
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    # 4) Обробка тексту після “Пошук” (MessageHandler)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_result),
        group=0
    )

    # 5) “📢 Розсилка” (CallbackQuery + MessageHandler)
    app.add_handler(
        CallbackQueryHandler(admin_broadcast, pattern=f"^{CB.ADMIN_BROADCAST.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
