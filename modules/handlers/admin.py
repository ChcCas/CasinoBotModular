# modules/handlers/admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, Application
from modules.keyboards import admin_panel_kb, client_menu, nav_buttons
from modules.callbacks import CB
from modules.states import STEP_MENU, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST
from modules.db import authorize_card, search_user, broadcast_to_all

# ─── 1) Підтвердження картки клієнта (callback_data = "admin_confirm_card:<user_id>:<card>") ───
async def admin_confirm_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    # callback_data формат: "admin_confirm_card:<user_id>:<card>"
    _, user_id_str, card = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)

    # 1) Зберігаємо в БД (authorize_card оновлює або створює запис у clients)
    authorize_card(user_id, card)

    # 2) Повідомляємо клієнта про успішну авторизацію
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Ваша картка {card} підтверджена. Ви успішно авторизовані.",
        reply_markup=client_menu(is_authorized=True)
    )

    # 3) Оновлюємо повідомлення адміну з інформацією про успіх
    await update.callback_query.message.edit_text(
        f"✅ Картка {card} для користувача {user_id} підтверджена."
    )

# ─── 2) Показуємо адмін-панель (натискання «🛠 Адмін-панель») ───
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🛠 Адмін-панель:", 
        reply_markup=admin_panel_kb()
    )
    return STEP_ADMIN_SEARCH

# ─── 3) Початок сценарію «Пошук клієнта» (натискання «🔍 Пошук клієнта») ───
async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Адмін натиснув «🔍 Пошук клієнта». 
    Просимо ввести ID або номер картки.
    """
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🔍 Введіть ID або номер картки для пошуку:",
        reply_markup=nav_buttons()
    )
    return STEP_ADMIN_BROADCAST  # після введення тексту переходимо у admin_broadcast

# ─── 4) Обробка тексту у сценарії «Пошук клієнта» ───
async def admin_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Після введення ID або картки адміністратор отримує результат пошуку:
    використовуємо search_user(query).
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

    await update.message.reply_text(text, reply_markup=nav_buttons())
    return STEP_MENU

# ─── 5) Сценарій «Розсилка» (натискання «📢 Розсилка») ───
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Адмін натиснув «📢 Розсилка» → питаємо текст →
    коли адміністратор вводить текст, викликаємо broadcast_to_all.
    """
    if update.callback_query:
        # це був CallbackQuery – ми відповіли на натискання «📢 Розсилка»
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "📢 Введіть текст для розсилки всім клієнтам:",
            reply_markup=nav_buttons()
        )
        return STEP_ADMIN_BROADCAST

    # Якщо це Message (адмін вводить сам текст розсилки)
    text_to_send = update.message.text.strip()
    broadcast_to_all(text_to_send)
    await update.message.reply_text(
        "✅ Розсилка успішно надіслана всім клієнтам.",
        reply_markup=nav_buttons()
    )
    return STEP_MENU

def register_admin_handlers(app: Application) -> None:
    """
    Регіструємо всі адмінські хендлери:
     1) admin_confirm_card  (callback_data="admin_confirm_card:<user_id>:<card>")
     2) show_admin_panel    (callback_data="admin_panel")
     3) admin_search        (callback_data="admin_search")
     4) admin_search_result (результат пошуку — MessageHandler)
     5) admin_broadcast     (callback_data="admin_broadcast" + MessageHandler)
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

    # 3) «🔍 Пошук клієнта» (переходимо до вводу тексту)
    app.add_handler(
        CallbackQueryHandler(admin_search, pattern=f"^{CB.ADMIN_SEARCH.value}$"),
        group=0
    )
    # 4) Обробка результату пошуку (MessageHandler)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_result),
        group=0
    )

    # 5) «📢 Розсилка» (CallbackQueryHandler → MessageHandler)
    app.add_handler(
        CallbackQueryHandler(admin_broadcast, pattern=f"^{CB.ADMIN_BROADCAST.value}$"),
        group=0
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast),
        group=0
    )
