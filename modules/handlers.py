from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
import re
import sqlite3
from modules.config import ADMIN_ID, DB_NAME

# === Стан ===
(
    STEP_MENU,
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
) = range(6)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_MENU: [CallbackQueryHandler(menu_handler)],
            STEP_CLIENT_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
            STEP_PROVIDER: [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT: [CallbackQueryHandler(process_payment)],
            STEP_CONFIRM_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file)],
            STEP_CONFIRMATION: [CallbackQueryHandler(confirm_submission)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(conv)

def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Я Клієнт", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")]
    ]
    user = update.effective_user
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    text = "Вітаємо у Casino Club Telegram Bot! Оберіть дію:"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "admin_panel":
        keyboard = [
            [InlineKeyboardButton("💰 Усі поповнення", callback_data="admin_deposits")],
            [InlineKeyboardButton("👤 Зареєстровані користувачі", callback_data="admin_users")],
            [InlineKeyboardButton("📄 Заявки на виведення", callback_data="admin_withdrawals")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
        ]
        await query.message.reply_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(keyboard))
        return STEP_MENU

    if query.data == "admin_deposits":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT username, card, provider, payment, timestamp FROM deposits ORDER BY timestamp DESC LIMIT 10")
            rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("Записів не знайдено.")
        else:
            text = "\n\n".join([f"👤 {r[0] or '—'}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\n🕒 {r[4]}" for r in rows])
            await query.message.reply_text(f"Останні поповнення:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("Немає зареєстрованих користувачів.")
        else:
            text = "\n\n".join([f"👤 Ім’я: {r[0]}\n📞 Телефон: {r[1]}\nСтатус: {r[2]}" for r in rows])
            await query.message.reply_text(f"Останні користувачі:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount TEXT,
                method TEXT,
                details TEXT,
                source_code TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("SELECT username, amount, method, details, source_code, timestamp FROM withdrawals ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("Заявок на виведення немає.")
        else:
            text = "\n\n".join([f"👤 {r[0] or '—'}\n💸 Сума: {r[1]}\n💳 Метод: {r[2]}\n📥 Реквізити: {r[3]}\n🔢 Код: {r[4]}\n🕒 {r[5]}" for r in rows])
            await query.message.reply_text(f"Останні заявки на виведення:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM registrations")
            users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM deposits")
            deposits = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM withdrawals")
            withdrawals = cur.fetchone()[0]
        text = f"📊 Статистика:\n👤 Користувачів: {users}\n💰 Поповнень: {deposits}\n📄 Виведень: {withdrawals}"
        await query.message.reply_text(text)
        return STEP_MENU

    if query.data == "client":
        await query.message.reply_text("Введіть номер картки клієнта клубу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if query.data in ("back", "home"):
        return await start(update, context)

    await query.message.reply_text("Ця функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU
