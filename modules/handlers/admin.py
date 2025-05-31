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
    Обробляє callback_data="admin_confirm_card:<user_id>:<card>".
    1) Зберігаємо картку у базі (authorize_card).
    2) Повідомляємо клієнта, що картка підтверджена, і показуємо client_menu(is_authorized=True).
    3) Редагуємо повідомлення адміну.
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо картку
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
        msg = str(e)
        if "Message is not modified" not in msg and "Message to edit not found" not in msg:
            raise
    return

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показує головне повідомлення адмін-панелі з клавіатурою admin_panel_kb.
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
    Коли адміністратор натиснув “🔍 Пошук клієнта” (callback_data="admin_search").
    Редагуємо повідомлення та переводимо у стан STEP_ADMIN_BROADCAST (очікуємо введення).
    """
    await update.callback_query.answer()
    base_id = context.user_data.get("base_msg_id")
    new_text = "🔍 Введіть ID або картку для пошуку:"
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=new_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.callback_query.message.reply_text(
                    new_text,
                    reply_markup=nav_buttons()
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    return STEP_ADMIN_BROADCAST

async def admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє введення admin (MessageHandler). Пошук у БД через search_user.
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
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.message.reply_text(
                    text,
                    reply_markup=nav_buttons()
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    return STEP_MENU

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обробляє callback “📢 Розсилка” та сам текст для розсилки:
    - Якщо це callback_query → запитуємо текст для розсилки.
    - Якщо це MessageHandler (адмін вставив текст) → робимо broadcast_to_all.
    """
    if update.callback_query:
        await update.callback_query.answer()
        base_id = context.user_data.get("base_msg_id")
        new_text = "📢 Введіть текст для розсилки всім клієнтам:"
        if base_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=base_id,
                    text=new_text,
                    reply_markup=nav_buttons()
                )
            except BadRequest as e:
                msg = str(e)
                if "Message to edit not found" in msg or "Message is not modified" in msg:
                    sent = await update.callback_query.message.reply_text(
                        new_text,
                        reply_markup=nav_buttons()
                    )
                    context.user_data["base_msg_id"] = sent.message_id
                else:
                    raise
        return STEP_ADMIN_BROADCAST

    # Якщо це текст (MessageHandler)
    text_to_send = update.message.text.strip()
    broadcast_to_all(text_to_send)

    base_id = context.user_data.get("base_msg_id")
    final_text = "✅ Розсилка успішно відправлена всім клієнтам."
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=final_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            msg = str(e)
            if "Message to edit not found" in msg or "Message is not modified" in msg:
                sent = await update.message.reply_text(
                    final_text,
                    reply_markup=nav_buttons()
                )
                context.user_data["base_msg_id"] = sent.message_id
            else:
                raise
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    """
    Регіструємо всі адмінські хендлери (група 0):
      1) admin_confirm_card
      2) show_admin_panel
      3) admin_search + admin_search_result
      4) admin_broadcast (callback + текст)
    """
    app.add_handler(
        CallbackQueryHandler(admin_confirm_card, pattern=r"^admin_confirm_card:\d+:.+"),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_result),
        group=0
    )
    app.add_handler(
        CallbackQueryHandler(admin_broadcast, pattern=f"^{CB.ADMIN_BROADCAST.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
