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

# ——— Константи ———————————————————————————————
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIF_PATH = os.path.join(BASE_DIR, "welcome.gif")  # Переконайтеся, що цей файл існує

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

# ——— Стани ———————————————————————————————
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
) = range(20)


def init_db():
    """Ініціалізує базові таблиці."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                user_id    INTEGER PRIMARY KEY,
                phone      TEXT,
                card       TEXT,
                authorized INTEGER DEFAULT 0
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                card TEXT,
                provider TEXT,
                payment TEXT,
                amount REAL,
                file_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount REAL,
                method TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
        conn.commit()


def setup_handlers(app):
    init_db()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # головне меню
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # підменю клієнта
            STEP_CLIENT_MENU: [
                CallbackQueryHandler(client_menu_handler,
                                     pattern="^(client_profile|client_find_card)$"),
                CallbackQueryHandler(menu_handler,
                                     pattern="^(deposit|withdraw|register|help|home|back)$"),
            ],

            # “Мій профіль”
            STEP_PROFILE_ENTER_CARD:  [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card)],
            STEP_PROFILE_ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone)],
            STEP_PROFILE_ENTER_CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_code)],

            # “Дізнатися картку”
            STEP_FIND_CARD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_find_phone)],

            # меню авторизованого клієнта
            STEP_CLIENT_AUTH: [CallbackQueryHandler(authorized_menu_handler)],

            # депозит
            STEP_CLIENT_CARD:    [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
            STEP_PROVIDER:       [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT:        [CallbackQueryHandler(process_payment)],
            STEP_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_CONFIRM_FILE:   [MessageHandler(filters.Document.ALL|filters.PHOTO|filters.VIDEO, process_file)],
            STEP_CONFIRMATION:   [CallbackQueryHandler(confirm_submission)],

            # виведення
            STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(process_withdraw_method)],
            STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
            STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$")],

            # реєстрація
            STEP_REG_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            STEP_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            STEP_REG_CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, register_code)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)

    # адмін-reply
    app.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY,
                       admin_reply),
        group=1,
    )


def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


# ——— Меню авторизованого клієнта ——————————————————
async def show_authorized_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎁 Зняти кешбек",    callback_data="cashback")],
        [InlineKeyboardButton("💰 Поповнити",       callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",    callback_data="withdraw")],
        [InlineKeyboardButton("📖 Історія",         callback_data="history")],
        [InlineKeyboardButton("🔒 Вийти з профілю", callback_data="logout")],
        [InlineKeyboardButton("ℹ️ Допомога",        callback_data="help")],
    ]
    text = "Вітаємо в особистому профілі!"
    await update.effective_chat.send_message(text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CLIENT_AUTH


async def authorized_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query; await q.answer()
    data    = q.data
    user_id = q.from_user.id

    if data == "cashback":
        await q.message.reply_text("Сценарій зняття кешбеку тут…")
        return STEP_CLIENT_AUTH

    if data == "deposit":
        # підтягуємо картку з БД
        with sqlite3.connect(DB_NAME) as conn:
            row = conn.execute("SELECT card FROM clients WHERE user_id=?", (user_id,)).fetchone()
        if row and row[0]:
            context.user_data["card"] = row[0]
            kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
            kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
                       InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
            await q.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
            return STEP_PROVIDER
        # якщо картки нема — звичайний флоу
        await q.message.reply_text("Введіть номер картки:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if data == "withdraw":
        # картку теж підтягуємо
        with sqlite3.connect(DB_NAME) as conn:
            row = conn.execute("SELECT card FROM clients WHERE user_id=?", (user_id,)).fetchone()
        if row and row[0]:
            context.user_data["card"] = row[0]
        await q.message.reply_text("Введіть суму виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    if data == "history":
        await q.message.reply_text("Тут буде історія операцій…")
        return STEP_CLIENT_AUTH

    if data == "logout":
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("UPDATE clients SET authorized=0 WHERE user_id=?", (user_id,))
            conn.commit()
        await q.message.reply_text("Ви вийшли з профілю.", reply_markup=nav_buttons())
        return await start(update, context)

    if data == "help":
        await q.message.reply_text("Тут буде довідка…")
        return STEP_CLIENT_AUTH

    if data in ("home", "back"):
        return await start(update, context)

    await q.message.reply_text("Ще в розробці…")
    return STEP_CLIENT_AUTH


# ——— /start ——————————————————————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎲 КЛІЄНТ",      callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація",   callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",     callback_data="help")],
    ]
    if update.effective_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    caption = "Вітаємо у *BIG GAME MONEY!* Оберіть дію:"
    markup  = InlineKeyboardMarkup(kb)

    if update.message:
        with open(GIF_PATH, "rb") as gif:
            await update.message.reply_animation(
                gif, caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup
            )
    else:
        await update.callback_query.answer()
        with open(GIF_PATH, "rb") as gif:
            await update.callback_query.message.reply_animation(
                gif, caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup
            )
    return STEP_MENU


# ——— Головне меню ——————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query; await q.answer()
    data = q.data

    if data == "admin_panel":
        kb = [
            [InlineKeyboardButton("💰 Депозити",    callback_data="admin_deposits")],
            [InlineKeyboardButton("👤 Користувачі",  callback_data="admin_users")],
            [InlineKeyboardButton("📄 Виведення",    callback_data="admin_withdrawals")],
            [InlineKeyboardButton("📊 Статистика",  callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await q.message.reply_text("Панель адміністратора:",
            reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    if data == "client":
        return await client_menu_handler(update, context)

    if data == "deposit":
        await q.message.reply_text("Введіть номер картки:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if data == "withdraw":
        await q.message.reply_text("Введіть суму виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    if data == "register":
        await q.message.reply_text("Введіть ім'я чи нік:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    if data == "help":
        await q.message.reply_text(
            "📖 *Довідка*\n• /start — меню\n• 🎲 Клієнт — ваш профіль\n…",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=nav_buttons()
        )
        return STEP_MENU

    if data in ("back", "home"):
        return await start(update, context)

    return STEP_MENU


# ——— Підменю “Клієнт” ——————————————————————————————
async def client_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()

    # перевіряємо авторизацію
    with sqlite3.connect(DB_NAME) as conn:
        auth = conn.execute(
            "SELECT authorized FROM clients WHERE user_id=?", (q.from_user.id,)
        ).fetchone()
    if auth and auth[0] == 1 and q.data == "client":
        return await show_authorized_menu(update, context)

    try:
        await q.message.delete()
    except:
        pass

    kb = [
        [InlineKeyboardButton("💳 Мій профіль",             callback_data="client_profile")],
        [InlineKeyboardButton("📇 Дізнатися номер картки", callback_data="client_find_card")],
        [InlineKeyboardButton("💰 Поповнити",              callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",            callback_data="withdraw")],
        [InlineKeyboardButton("🏠 Головне меню",            callback_data="home")],
    ]
    await q.message.reply_text("Оберіть опцію:", reply_markup=InlineKeyboardMarkup(kb))

    if q.data == "client_profile":
        await q.message.reply_text("Введіть номер картки:", reply_markup=nav_buttons())
        context.user_data["profile_mode"] = "direct"
        return STEP_PROFILE_ENTER_CARD

    if q.data == "client_find_card":
        await q.message.reply_text("Введіть телефон:", reply_markup=nav_buttons())
        context.user_data["profile_mode"] = "find"
        return STEP_PROFILE_ENTER_PHONE

    return STEP_CLIENT_MENU


# ——— “Мій профіль” — прямий ввід картки —————————————————
async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,7}", card):
        await update.message.reply_text("Невірний формат картки.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CARD
    context.user_data["profile_card"] = card
    await update.message.reply_text("Тепер введіть телефон:", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_PHONE


# ——— “Мій профіль” — ввід телефону ————————————————————
async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("Невірний формат телефону.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_PHONE

    mode    = context.user_data.get("profile_mode")
    user_id = update.effective_user.id

    if mode == "direct":
        card = context.user_data["profile_card"]
        await context.bot.send_message(
            ADMIN_ID, f"Авторизація клієнта\nКартка: {card}\nТелефон: {phone}"
        )
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO clients(user_id,phone,card,authorized) VALUES(?,?,?,1)",
                (user_id, phone, card)
            )
            conn.commit()
        await update.message.reply_text("Авторизація успішна ✅", reply_markup=nav_buttons())
        return await show_authorized_menu(update, context)

    # режим “find”
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO clients(user_id,phone,authorized) VALUES(?,?,0)",
            (user_id, phone)
        )
        conn.commit()
    await context.bot.send_message(
        ADMIN_ID, f"Хоче дізнатися свій номер картки\nТелефон: {phone}"
    )
    await update.message.reply_text("Введіть код із SMS:", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_CODE


# ——— “Мій профіль” — код підтвердження —————————————————
async def profile_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CODE

    user_id = update.effective_user.id
    msg = await context.bot.send_message(ADMIN_ID, f"Код для {user_id}: {code}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id) VALUES(?,?)",
            (msg.message_id, user_id)
        )
        conn.commit()

    await update.message.reply_text("Код відправлено адміністратору. Чекайте…", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— “Дізнатися картку” за телефоном ——————————————————
async def profile_find_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("Невірний формат телефону.", reply_markup=nav_buttons())
        return STEP_FIND_CARD_PHONE

    await context.bot.send_message(
        ADMIN_ID, f"Хоче дізнатися свій номер картки\nТелефон: {phone}"
    )
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO clients(user_id,phone,authorized) VALUES(?,?,0)",
            (update.effective_user.id, phone)
        )
        conn.commit()
    await update.message.reply_text("Введіть код із SMS:", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_CODE


# ——— Адмін-reply ——————————————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id FROM threads WHERE admin_msg_id = ?", (orig,)
        ).fetchone()
    if not row:
        await update.message.reply_text("Ланцюг не знайдено.")
        return
    tgt = row[0]

    # якщо клієнт не авторизований — обробляємо як картку
    with sqlite3.connect(DB_NAME) as conn:
        auth = conn.execute(
            "SELECT authorized FROM clients WHERE user_id = ?", (tgt,)
        ).fetchone()
    if auth and auth[0] == 0:
        card = update.message.text.strip()
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "UPDATE clients SET card = ?, authorized = 1 WHERE user_id = ?",
                (card, tgt)
            )
            conn.commit()
        await context.bot.send_message(
            tgt, f"Ваш номер картки: {card}\nАвторизація успішна ✅"
        )
        return

    # звичайний reply
    await context.bot.send_message(tgt, update.message.text)
    await update.message.reply_text("✅ Доставлено.")


# ——— Флоу депозиту ——————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", text):
        await update.message.reply_text("Невірний формат картки.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = text
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data in ("back","home"):
        return await menu_handler(update, context)
    context.user_data["provider"] = q.data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await q.message.reply_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data in ("back","home"):
        return await menu_handler(update, context)
    context.user_data["payment"] = q.data
    await q.message.reply_text("Введіть суму депозиту:", reply_markup=nav_buttons())
    return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text.strip())
        if amt <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT
    context.user_data["deposit_amount"] = amt
    await update.message.reply_text("Надішліть підтвердження (документ/фото/відео):", reply_markup=nav_buttons())
    return STEP_CONFIRM_FILE

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Підтвердьте надсилання:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query; await q.answer()
    user    = q.from_user
    card    = context.user_data["card"]
    prov    = context.user_data["provider"]
    pay     = context.user_data["payment"]
    amount  = context.user_data["deposit_amount"]
    file_msg: Message = context.user_data["file"]

    caption = (
        f"Депозит:\nКартка: {card}\nПровайдер: {prov}\n"
        f"Оплата: {pay}\nСума: {amount}"
    )
    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id) VALUES(?,?)",
            (admin_msg.message_id, user.id)
        )
        conn.execute(
            "INSERT INTO deposits(user_id,username,card,provider,payment,amount,file_type) "
            "VALUES(?,?,?,?,?,?,?)",
            (user.id, user.username or "", card, prov, pay, amount,
             file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await q.message.reply_text("Депозит надіслано ✅", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу виведення ——————————————————————————————
async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text.strip())
        if amt <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT
    context.user_data["withdraw_amount"] = amt
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.message.reply_text("Оберіть метод виведення:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data in ("back","home"):
        return await menu_handler(update, context)
    context.user_data["withdraw_method"] = q.data
    await q.message.reply_text("Введіть реквізити:", reply_markup=nav_buttons())
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details
    amt    = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    text = f"Підтвердити виведення?\nСума: {amt}\nМетод: {method}\nРеквізити: {details}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("◀️ Назад",       callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.message.reply_text(text, reply_markup=kb)
    return STEP_WITHDRAW_CONFIRM

async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    user    = q.from_user
    amt     = context.user_data["withdraw_amount"]
    method  = context.user_data["withdraw_method"]
    details = context.user_data["withdraw_details"]

    summary = f"Виведення:\nСума: {amt}\nМетод: {method}\nРеквізити: {details}"
    admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=summary)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO withdrawals(user_id,username,amount,method,details) VALUES(?,?,?,?,?)",
            (user.id, user.username or "", amt, method, details)
        )
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id) VALUES(?,?)",
            (admin_msg.message_id, user.id)
        )
        conn.commit()

    await q.message.reply_text("Заявка на виведення надіслана ✅", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу реєстрації ——————————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть телефон:", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("Невірний формат телефону.", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    name    = context.user_data["reg_name"]
    user_id = update.effective_user.id

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Нова реєстрація\nІм'я: {name}\nТелефон: {phone}"
    )
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO registrations(user_id,name,phone) VALUES(?,?,?)",
            (user_id, name, phone)
        )
        conn.commit()

    await update.message.reply_text("Введіть 4-значний код із SMS:", reply_markup=nav_buttons())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код.", reply_markup=nav_buttons())
        return STEP_REG_CODE
    name    = context.user_data["reg_name"]
    user_id = update.effective_user.id

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код реєстрації {code} від {name} ({user_id})"
    )
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id) VALUES(?,?)",
            (msg.message_id, user_id)
        )
        conn.commit()

    await update.message.reply_text("Код відправлено адміністратору. Чекайте…", reply_markup=nav_buttons())
    return STEP_MENU
