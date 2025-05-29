import os
import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from modules.config import ADMIN_ID, DB_NAME

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIF_PATH     = os.path.join(PROJECT_ROOT, "welcome.gif")

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

(
    STEP_MENU,
    STEP_CLIENT_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
    STEP_FIND_CARD_PHONE,
    STEP_CLIENT_AUTH,
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_DEPOSIT_AMOUNT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
    STEP_ADMIN_BROADCAST,
    STEP_ADMIN_SEARCH,
) = range(22)

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS threads (admin_msg_id INTEGER PRIMARY KEY, user_id INTEGER)")
        conn.execute("CREATE TABLE IF NOT EXISTS clients (user_id INTEGER PRIMARY KEY, phone TEXT, card TEXT, authorized INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS deposits (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, card TEXT, provider TEXT, payment TEXT, amount REAL, file_type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, amount REAL, method TEXT, details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS registrations (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, phone TEXT, status TEXT DEFAULT 'pending', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()

def setup_handlers(app):
    init_db()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply), group=1)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 КЛІЄНТ", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = "Вітаємо у *BIG GAME MONEY!* Оберіть дію:"

    if update.message:
        with open(GIF_PATH, "rb") as gif:
            await update.message.reply_animation(gif, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        with open(GIF_PATH, "rb") as gif:
            await update.callback_query.message.reply_animation(gif, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    return STEP_MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_panel":
        return await show_admin_panel(query)

    elif data == "admin_deposits":
        await query.message.reply_text("📥 Останні депозити:\n(підключи логіку)", reply_markup=admin_nav())
        return STEP_MENU

    elif data == "admin_users":
        await query.message.reply_text("👥 Зареєстровані користувачі:\n(підключи логіку)", reply_markup=admin_nav())
        return STEP_MENU

    elif data == "admin_withdrawals":
        await query.message.reply_text("📤 Запити на виведення:\n(підключи логіку)", reply_markup=admin_nav())
        return STEP_MENU

    elif data == "admin_stats":
        await query.message.reply_text("📊 Статистика:\n(підключи логіку)", reply_markup=admin_nav())
        return STEP_MENU

    elif data == "admin_search":
        await query.message.reply_text("🔍 Введіть ID або номер телефону:", reply_markup=admin_nav())
        return STEP_ADMIN_SEARCH

    elif data == "admin_broadcast":
        await query.message.reply_text("📢 Введіть текст для розсилки:", reply_markup=admin_nav())
        return STEP_ADMIN_BROADCAST

    elif data == "home" or data == "back":
        return await start(update, context)

    elif data == "client":
        await query.message.reply_text("💳 Мій профіль\n(підключи логіку профілю)", reply_markup=client_nav())
        return STEP_MENU

    elif data == "deposit":
        await query.message.reply_text("💸 Введіть суму для поповнення:", reply_markup=client_nav())
        return STEP_MENU

    elif data == "withdraw":
        await query.message.reply_text("💳 Введіть суму для виведення:", reply_markup=client_nav())
        return STEP_MENU

    elif data == "register":
        await query.message.reply_text("📝 Введіть ваше ім’я:", reply_markup=client_nav())
        return STEP_MENU

    elif data == "help":
        await query.message.reply_text("ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат", reply_markup=client_nav())
        return STEP_MENU

    return STEP_MENU


async def show_admin_panel(query):
    keyboard = [
        [
            InlineKeyboardButton("💰 Депозити", callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення", callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта", callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка", callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.reply_text("🛠 Адмін-панель:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_MENU


def admin_nav():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


def client_nav():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="client")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
# ——— Реєстрація клієнта ——————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["reg_name"] = name
    await update.message.reply_text("📞 Введіть номер телефону (0XXXXXXXXX):", reply_markup=client_nav())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.match(r"^0\d{9}$", phone):
        await update.message.reply_text("❗️ Невірний формат. Спробуйте ще раз:", reply_markup=client_nav())
        return STEP_REG_PHONE
    context.user_data["reg_phone"] = phone
    await update.message.reply_text("🔑 Введіть 4-значний код підтвердження:", reply_markup=client_nav())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.match(r"^\d{4}$", code):
        await update.message.reply_text("❗️ Код має складатись з 4 цифр.", reply_markup=client_nav())
        return STEP_REG_CODE

    user_id = update.effective_user.id
    name = context.user_data.get("reg_name")
    phone = context.user_data.get("reg_phone")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO registrations (user_id, name, phone) VALUES (?, ?, ?)", (user_id, name, phone))
        conn.commit()

    await update.message.reply_text("✅ Реєстрація успішна! Оберіть дію:", reply_markup=client_nav())
    return STEP_MENU


# ——— Поповнення ————————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip().replace(" ", "")
    if not re.match(r"^\d{16}$", card):
        await update.message.reply_text("❗️ Введіть коректний 16-значний номер картки:", reply_markup=client_nav())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card

    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ])
    await update.message.reply_text("🎰 Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_PROVIDER


async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provider = update.callback_query.data
    context.user_data["provider"] = provider

    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ])
    await update.callback_query.message.reply_text("💳 Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_PAYMENT


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["payment"] = update.callback_query.data
    await update.callback_query.message.reply_text("💰 Введіть суму поповнення:", reply_markup=client_nav())
    return STEP_DEPOSIT_AMOUNT


async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❗️ Введіть коректну суму:", reply_markup=client_nav())
        return STEP_DEPOSIT_AMOUNT

    context.user_data["amount"] = amount
    await update.message.reply_text("📎 Надішліть підтвердження (фото, документ або відео):", reply_markup=client_nav())
    return STEP_CONFIRM_FILE


async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_type = "unknown"
    if update.message.document:
        file_type = "document"
    elif update.message.photo:
        file_type = "photo"
    elif update.message.video:
        file_type = "video"

    context.user_data["file_type"] = file_type
    await update.message.reply_text("✅ Натисніть підтвердити:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]))
    return STEP_CONFIRMATION


async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    card     = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment  = context.user_data.get("payment")
    amount   = context.user_data.get("amount")
    ftype    = context.user_data.get("file_type")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO deposits (user_id, username, card, provider, payment, amount, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user.id, user.username, card, provider, payment, amount, ftype))
        conn.commit()

    await update.callback_query.message.reply_text("💸 Поповнення збережено! Очікуйте підтвердження.", reply_markup=client_nav())
    return STEP_MENU


# ——— Виведення коштів ————————————————————————————
async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
        context.user_data["withdraw_amount"] = amount
        kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
        kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
                   InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
        await update.message.reply_text("Оберіть метод виведення:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_WITHDRAW_METHOD
    except ValueError:
        await update.message.reply_text("❗️ Введіть коректну суму:", reply_markup=client_nav())
        return STEP_WITHDRAW_AMOUNT


async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method
    await update.callback_query.message.reply_text("💳 Введіть реквізити (номер картки або гаманець):", reply_markup=client_nav())
    return STEP_WITHDRAW_DETAILS


async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["withdraw_details"] = update.message.text.strip()
    await update.message.reply_text("✅ Підтвердити виведення?", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]))
    return STEP_WITHDRAW_CONFIRM


async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    amount = context.user_data.get("withdraw_amount")
    method = context.user_data.get("withdraw_method")
    details = context.user_data.get("withdraw_details")

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO withdrawals (user_id, username, amount, method, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user.id, user.username, amount, method, details))
        conn.commit()

    await update.callback_query.message.reply_text("✅ Запит на виведення надіслано!", reply_markup=client_nav())
    return STEP_MENU