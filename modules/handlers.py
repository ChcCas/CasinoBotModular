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

# ——— Константи —————————————————————————————————
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIF_PATH = os.path.join(BASE_DIR, "welcome.gif")  # Переконайтеся, що welcome.gif лежить тут

# ——— Стани ———————————————————————————————
(
    STEP_MENU,
    STEP_CLIENT_MENU,
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
    STEP_FIND_CARD_PHONE,
) = range(16)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]


def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # Підменю клієнта
            STEP_CLIENT_MENU: [CallbackQueryHandler(client_menu_handler)],

            # Депозит
            STEP_CLIENT_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_PROVIDER: [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT: [CallbackQueryHandler(process_payment)],
            STEP_DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],
            STEP_CONFIRM_FILE: [
                MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file)
            ],
            STEP_CONFIRMATION: [CallbackQueryHandler(confirm_submission)],

            # Виведення
            STEP_WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_METHOD: [
                CallbackQueryHandler(process_withdraw_method),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_CONFIRM: [
                CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$"),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],

            # Реєстрація
            STEP_REG_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_REG_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_REG_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],

            # Підім’я «Дізнатися номер картки»
            STEP_FIND_CARD_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_card_by_phone),
                CallbackQueryHandler(client_menu_handler, pattern="^(back|home)$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)

    # Reply-хендлер адміністратора
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1,
    )


def nav_buttons():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("◀️ Назад", callback_data="back")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
    )


# ——— /start з GIF-привітанням ————————————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 КЛІЄНТ", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")]
        )
    markup = InlineKeyboardMarkup(keyboard)

    caption = "Вітаємо у *BIG GAME MONEY!* Оберіть дію:"
    if update.message:
        with open(GIF_PATH, "rb") as gif:
            await update.message.reply_animation(
                animation=gif,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup,
            )
    else:
        await update.callback_query.answer()
        with open(GIF_PATH, "rb") as gif:
            await update.callback_query.message.reply_animation(
                animation=gif,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup,
            )

    return STEP_MENU


# ——— Головне меню —————————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    is_admin = query.from_user.id == ADMIN_ID
    if not is_admin:
        try:
            await query.message.delete()
        except:
            pass

    data = query.data

    if data == "admin_panel":
        kb = [
            [InlineKeyboardButton("💰 Усі поповнення", callback_data="admin_deposits")],
            [InlineKeyboardButton("👤 Зареєстровані користувачі", callback_data="admin_users")],
            [InlineKeyboardButton("📄 Заявки на виведення", callback_data="admin_withdrawals")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.reply_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    # Перехід до клієнтського підменю
    if data in ("client", "deposit", "withdraw", "register", "help"):
        return await client_menu_handler(update, context)

    # Обробка адмін-запитів
    if data == "admin_deposits":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, card, provider, payment, amount, timestamp "
                "FROM deposits ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = "Записів не знайдено." if not rows else "\n\n".join(
            f"👤 {r[0] or '—'}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\nСума: {r[4]}\n🕒 {r[5]}"
            for r in rows
        )
        await query.message.reply_text(f"Останні поповнення:\n\n{text}")
        return STEP_MENU

    if data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = "Немає зареєстрованих." if not rows else "\n\n".join(
            f"👤 {r[0]}\n📞 {r[1]}\nСтатус: {r[2]}" for r in rows
        )
        await query.message.reply_text(f"Останні користувачі:\n\n{text}")
        return STEP_MENU

    if data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, amount, method, details, timestamp "
                "FROM withdrawals ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = "Заявок немає." if not rows else "\n\n".join(
            f"👤 {r[0]}\n💸 {r[1]}\nМетод: {r[2]}\nРеквізити: {r[3]}\n🕒 {r[4]}"
            for r in rows
        )
        await query.message.reply_text(f"Останні заявки:\n\n{text}")
        return STEP_MENU

    if data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            users = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            deps = conn.execute("SELECT COUNT(*) FROM deposits").fetchone()[0]
            wds = conn.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        await query.message.reply_text(
            f"📊 Статистика:\n👤 Користувачів: {users}\n💰 Депозити: {deps}\n📄 Виведення: {wds}"
        )
        return STEP_MENU

    if data in ("back", "home"):
        return await start(update, context)

    await query.message.reply_text("Функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Підменю “КЛІЄНТ” —————————————————————————————
async def client_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass

    keyboard = [
        [InlineKeyboardButton("💳 Мій профіль", callback_data="client_profile")],
        [InlineKeyboardButton("📇 Дізнатися номер картки", callback_data="client_find_card")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.reply_text("Оберіть опцію:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_CLIENT_MENU


# ——— “Мій профіль” —————————————————————————————
async def client_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT card, amount FROM deposits WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        card = row[0] if row else "Не вказана"
        # Баланс
        cur.execute("SELECT SUM(amount) FROM deposits WHERE user_id = ?", (user_id,))
        dep_sum = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(amount) FROM withdrawals WHERE user_id = ?", (user_id,))
        wd_sum = cur.fetchone()[0] or 0

    balance = dep_sum - wd_sum
    cashback = round(dep_sum * 0.01, 2)

    text = (
        "*Мій профіль*\n"
        f"🔑 Картка: `{card}`\n"
        f"💰 Поповнено: {dep_sum}\n"
        f"💸 Виведено: {wd_sum}\n"
        f"💼 Баланс: {balance}\n"
        f"🎁 Кешбек (1%): {cashback}"
    )
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— “Дізнатися номер картки” ————————————————————
async def find_card_by_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний телефон.", reply_markup=nav_buttons())
        return STEP_FIND_CARD_PHONE

    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id FROM registrations WHERE phone = ?", (phone,)).fetchone()
    if not row:
        await update.message.reply_text("Не знайдено.", reply_markup=nav_buttons())
    else:
        uid = row[0]
        with sqlite3.connect(DB_NAME) as conn:
            card_row = conn.execute(
                "SELECT card FROM deposits WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (uid,)
            ).fetchone()
        card = card_row[0] if card_row else "Не знайена"
        await update.message.reply_text(f"Ваша картка: {card}", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу “Депозит” —————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний номер.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER


async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data in ("back", "home"):
        return await client_menu_handler(update, context)
    context.user_data["provider"] = data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await query.message.reply_text("Оберіть спосіб оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data in ("back", "home"):
        return await client_menu_handler(update, context)
    context.user_data["payment"] = data
    await query.message.reply_text("Введіть суму поповнення:", reply_markup=nav_buttons())
    return STEP_DEPOSIT_AMOUNT


async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amt = float(text)
        if amt <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT
    context.user_data["deposit_amount"] = amt
    await update.message.reply_text("Завантажте підтвердження (документ/фото/відео):", reply_markup=nav_buttons())
    return STEP_CONFIRM_FILE


async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Підтвердіть надсилання:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION


async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    card = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    amount = context.user_data.get("deposit_amount")
    file_msg: Message = context.user_data.get("file")

    caption = (
        f"Заявка на депозит:\n"
        f"Картка: {card}\n"
        f"Провайдер: {provider}\n"
        f"Оплата: {payment}\n"
        f"Сума: {amount}"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER,
                user_msg_id   INTEGER
            )
        """)
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
            )
        """)
        conn.commit()

    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id, user_msg_id) VALUES (?, ?, ?)",
            (admin_msg.message_id, user.id, file_msg.message_id),
        )
        conn.execute(
            "INSERT INTO deposits(user_id, username, card, provider, payment, amount, file_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.username or "", card, provider, payment, amount,
             file_msg.effective_attachment.__class__.__name__),
        )
        conn.commit()

    await query.message.reply_text("Дякуємо! Депозит відправлено.", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу “Виведення” —————————————————————————————
async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amt = float(text)
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
    query = update.callback_query
    await query.answer()
    method = query.data
    if method in ("back", "home"):
        return await client_menu_handler(update, context)
    context.user_data["withdraw_method"] = method
    await query.message.reply_text("Введіть реквізити:", reply_markup=nav_buttons())
    return STEP_WITHDRAW_DETAILS


async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details
    amt = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    text = (
        f"Підтвердити виведення?\n"
        f"Сума: {amt}\nМетод: {method}\nРеквізити: {details}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.message.reply_text(text, reply_markup=kb)
    return STEP_WITHDRAW_CONFIRM


async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    amt = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    details = context.user_data["withdraw_details"]

    text = (
        f"Заявка на виведення:\n"
        f"Сума: {amt}\nМетод: {method}\nРеквізити: {details}"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount REAL,
                method TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO withdrawals(user_id, username, amount, method, details) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username or "", amt, method, details),
        )
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id, user_msg_id) VALUES (?, ?, ?)",
            (admin_msg.message_id, user.id, 0),
        )
        conn.commit()

    await query.message.reply_text("Заявка на виведення відправлена.", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу “Реєстрація” ———————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть телефон (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний телефон.", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    context.user_data["reg_phone"] = phone
    name = context.user_data["reg_name"]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Реєстрація: {name}, {phone}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("INSERT INTO registrations(user_id, name, phone) VALUES (?, ?, ?)",
                     (update.effective_user.id, name, phone))
        conn.commit()
    await update.message.reply_text("Введіть 4-значний код:", reply_markup=nav_buttons())
    return STEP_REG_CODE


async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код.", reply_markup=nav_buttons())
        return STEP_REG_CODE
    name = context.user_data["reg_name"]
    user = update.effective_user
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Код {code} від {name} ({user.id})")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])
    await update.message.reply_text("Реєстрацію надіслано!", reply_markup=kb)
    return STEP_CLIENT_MENU


# ——— Хендлер відповіді адміна —————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    admin_msg_id = orig.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id FROM threads WHERE admin_msg_id = ?", (admin_msg_id,)).fetchone()
    if not row:
        await update.message.reply_text("Не знайдено.")
        return
    user_id = row[0]
    await context.bot.send_message(chat_id=user_id, text=update.message.text)
    await update.message.reply_text("✅ Доставлено.")
