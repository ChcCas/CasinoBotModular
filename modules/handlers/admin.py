# modules/handlers/admin.py

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.config import ADMIN_ID, DB_NAME
from modules.db import search_user, list_all_clients, authorize_card
from modules.keyboards import admin_panel_kb, nav_buttons, client_menu
from modules.callbacks import CB
from modules.states import (
    STEP_MENU,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST
)

# ───────────────────────────────────────────────────────────────────────────────
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Викликається, коли адміністратор натискає кнопку “🛠 Адмін-панель”.
    Відправляє клавіатуру admin_panel_kb().
    """
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🛠 Адмін-панель:",
        reply_markup=admin_panel_kb()
    )
    return STEP_MENU

# ───────────────────────────────────────────────────────────────────────────────
async def admin_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Адмін натиснув “🔍 Пошук клієнта”.
    Запитуємо ID або номер картки.
    """
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "🔍 Введіть ID або картку для пошуку:",
        reply_markup=nav_buttons()
    )
    context.user_data["admin_search_msg"] = msg.message_id
    return STEP_ADMIN_SEARCH

async def admin_search_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отримуємо текст від адміністратора — ID або картку.
    Шукаємо в БД і повертаємо результати.
    """
    query = update.message.text.strip()
    record = search_user(query)

    base_msg_id = context.user_data.get("admin_search_msg")
    chat_id = update.effective_chat.id

    if record:
        text = (
            f"✅ Користувача знайдено!\n\n"
            f"• User ID: {record['user_id']}\n"
            f"• Картка: {record['card']}\n"
            f"• Телефон: {record['phone'] or 'Не вказаний'}\n"
            f"• Підтверджено: {'Так' if record['confirmed'] else 'Ні'}"
        )
    else:
        text = "❌ Користувача з таким ID або карткою не знайдено."

    if base_msg_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=base_msg_id,
            text=text,
            reply_markup=admin_panel_kb()
        )
    else:
        await update.message.reply_text(text, reply_markup=admin_panel_kb())

    context.user_data.pop("admin_search_msg", None)
    return ConversationHandler.END

# ───────────────────────────────────────────────────────────────────────────────
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Адмін натиснув “📢 Розсилка”.
    Запитуємо текст для розсилки.
    """
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "📢 Введіть текст для розсилки всім підтвердженим користувачам:",
        reply_markup=nav_buttons()
    )
    context.user_data["admin_broadcast_msg"] = msg.message_id
    return STEP_ADMIN_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отримуємо текст від адміністратора і розсилаємо його всім підтвердженим користувачам.
    """
    text_to_send = update.message.text.strip()
    all_ids = list_all_clients()

    sent_count = 0
    for uid in all_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 Розсилка від адміністратора:\n\n{text_to_send}"
            )
            sent_count += 1
        except Exception:
            continue

    base_msg_id = context.user_data.get("admin_broadcast_msg")
    chat_id = update.effective_chat.id
    confirmation_text = f"✅ Розсилка надіслана {sent_count} користувачам."
    if base_msg_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=base_msg_id,
            text=confirmation_text,
            reply_markup=admin_panel_kb()
        )
    else:
        await update.message.reply_text(
            confirmation_text,
            reply_markup=admin_panel_kb()
        )

    context.user_data.pop("admin_broadcast_msg", None)
    return ConversationHandler.END

# ───────────────────────────────────────────────────────────────────────────────
async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отримує callback_data “admin_confirm_card:<user_id>:<card>”.
    Підтверджуємо картку в БД, повідомляємо клієнта й оновлюємо повідомлення адміну.
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо в БД (ставимо confirmed=1)
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

# ───────────────────────────────────────────────────────────────────────────────
def register_admin_handlers(app: Application) -> None:
    """
    Реєструє:
      1) show_admin_panel (кнопка “admin_panel”) — group=1
      2) admin_confirm_card — group=0
      3) ConversationHandler для admin_search — group=0
      4) ConversationHandler для admin_broadcast — group=0
    """

    # 1) Показ адмін-панелі
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=1
    )

    # 2) Підтвердження картки адміністратором
    app.add_handler(
        CallbackQueryHandler(
            admin_confirm_card,
            pattern=r"^admin_confirm_card:\d+:.+"
        ),
        group=0
    )

    # 3) ConversationHandler для пошуку клієнта
    admin_search_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_search_start, pattern="^admin_search$")
        ],
        states={
            STEP_ADMIN_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_find)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_admin_panel, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(show_admin_panel, pattern=f"^{CB.HOME.value}$")
        ],
        per_chat=True,  # <-- Замість per_message=True
    )
    app.add_handler(admin_search_conv, group=0)

    # 4) ConversationHandler для адмін-розсилки
    admin_broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$")
        ],
        states={
            STEP_ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_admin_panel, pattern=f"^{CB.BACK.value}$"),
            CallbackQueryHandler(show_admin_panel, pattern=f"^{CB.HOME.value}$")
        ],
        per_chat=True,  # <-- Замість per_message=True
    )
    app.add_handler(admin_broadcast_conv, group=0)
