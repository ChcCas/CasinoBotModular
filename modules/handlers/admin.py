# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.config import ADMIN_ID
from modules.db import authorize_card, search_user, broadcast_to_all
from modules.keyboards import admin_panel_kb, nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли адмін натиснув кнопку «✅ Підтвердити картку».
    callback_data = "admin_confirm_card:<user_id>:<card>"
    """
    await update.callback_query.answer()
    data = update.callback_query.data  # «admin_confirm_card:123456:4999887766554433»
    _, user_id_str, card = data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Додаємо / оновлюємо запис у таблиці clients
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта про успішну підтверджену картку
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані!",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Оновлюємо (редагуємо) повідомлення адміністратору
    try:
        await update.callback_query.message.edit_text(
            f"✅ Картка {card} для користувача {user_id} підтверджена."
        )
    except BadRequest as e:
        msg = str(e).lower()
        # Якщо повідомлення уже видалено чи текст не змінився — ігноруємо
        if ("message to edit not found" in msg) or ("message is not modified" in msg):
            pass
        else:
            raise

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли адмін натиснув «🛠 Адмін-панель».
    Показуємо клавіатуру адмінпанелі.
    """
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🛠 Адмін-панель:",
        reply_markup=admin_panel_kb()
    )
    return STEP_ADMIN_SEARCH

async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли адмін обрав «🔍 Пошук клієнта».
    Запитуємо ID або картку для пошуку.
    """
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🔍 Введіть ID або картку для пошуку:",
        reply_markup=nav_buttons()
    )
    return STEP_ADMIN_SEARCH

async def do_admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляємо введений текст (ID або картка), шукаємо у БД і повертаємо результат.
    """
    query_text = update.message.text.strip()
    found = search_user(query_text)
    if found:
        await update.message.reply_text(
            f"🟢 Знайдено клієнта:\n"
            f"ID: {found['user_id']}\n"
            f"Картка: {found['card']}"
        )
    else:
        await update.message.reply_text("❌ Клієнта не знайдено.")

    return STEP_MENU

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробник, коли адмін обрав «📢 Розсилка».
    Питаємо, який текст потрібно розіслати.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "📢 Введіть текст для розсилки:", reply_markup=nav_buttons()
    )
    return STEP_ADMIN_BROADCAST

async def do_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляємо текст і виконуємо розсилку всім користувачам із таблиці clients.
    """
    text = update.message.text.strip()
    broadcast_to_all(text)
    await update.message.reply_text("📢 Розсилка запущена.", reply_markup=nav_buttons())
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    """
    Регіструємо всі хендлери адміністратора (група 0):
      1) Підтвердження картки (admin_confirm_card)
      2) Кнопка «Адмін-панель» (show_admin_panel)
      3) Пошук клієнта (admin_search + do_admin_search)
      4) Розсилка (admin_broadcast + do_admin_broadcast)
    """
    # 1) Коли адмін натискає «✅ Підтвердити картку»
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )

    # 2) Коли адмін натискає «🛠 Адмін-панель»
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )

    # 3) Пошук клієнта: entry (callback) + message (Text)
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, do_admin_search),
        group=0
    )

    # 4) Розсилка: entry (callback) + message (Text)
    app.add_handler(
        CallbackQueryHandler(admin_broadcast, pattern=f"^{CB.ADMIN_BROADCAST.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, do_admin_broadcast),
        group=0
    )
