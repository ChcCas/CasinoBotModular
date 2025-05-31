# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.keyboards import admin_panel_kb, client_menu, nav_buttons
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from modules.db import authorize_card, search_user, broadcast_to_all

async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    CallbackQueryHandler для “admin_confirm_card:<user_id>:<card>”.
    Адмін натиснув “✅ Підтвердити картку”.
    Зберігаємо картку, повідомляємо клієнта, редагуємо своє повідомлення.
    """
    await update.callback_query.answer()
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    authorize_card(user_id, card)

    # Повідомляємо клієнта
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # Редагуємо повідомлення адміну
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
    CallbackQueryHandler для “admin_panel”.
    Надсилаємо/редагуємо повідомлення з адмін-панеллю і зберігаємо message_id.
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
    Редагуємо повідомлення адміну: “Введіть ID або картку для пошуку”.
    """
    await update.callback_query.answer()
    base_id = context.user_data.get("base_msg_id")
    new_text = "🔍 Введіть ID або номер картки для пошуку:"
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=new_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_ADMIN_BROADCAST

async def admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    MessageHandler після введення тексту адміністратором.
    Виконуємо search_user і редагуємо повідомлення з результатом.
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
            if "Message is not modified" not in str(e):
                raise
    return STEP_MENU

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) CallbackQueryHandler: адмiн натиснув “📢 Розсилка” → редагуємо повідомлення, питаємо текст.
    2) MessageHandler: адмiн ввів текст → виконуємо broadcast_to_all і редагуємо повідомлення з підтвердженням.
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
                if "Message is not modified" not in str(e):
                    raise
        return STEP_ADMIN_BROADCAST

    # Якщо це текст від адміну (розсилка)
    text_to_send = update.message.text.strip()
    broadcast_to_all(text_to_send)

    base_id = context.user_data.get("base_msg_id")
    final_text = "✅ Розсилка успішно надіслана всім клієнтам."
    if base_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=base_id,
                text=final_text,
                reply_markup=nav_buttons()
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
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
