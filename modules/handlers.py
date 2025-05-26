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
GIF_PATH = os.path.join(BASE_DIR, "welcome.gif")  # Перевірте, що welcome.gif лежить тут

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]

# ——— Стани ———————————————————————————————
(
    STEP_MENU,
    STEP_CLIENT_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
    STEP_FIND_CARD_PHONE,
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
) = range(19)


def init_db():
    """Ініціалізує таблиці `threads` та `clients`."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                user_id    INTEGER PRIMARY KEY,
                phone      TEXT,
                card       TEXT,
                authorized INTEGER DEFAULT 0
            )
        """)
        # deposits, withdrawals, registrations створюються у своїх флоу
        conn.commit()


def setup_handlers(application):
    init_db()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Головне меню
            STEP_MENU:               [CallbackQueryHandler(menu_handler)],

            # Підменю клієнта
            STEP_CLIENT_MENU:        [CallbackQueryHandler(client_menu_handler)],

            # Сценарій “Мій профіль”
            STEP_PROFILE_ENTER_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_card)],
            STEP_PROFILE_ENTER_PHONE:[MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_phone)],
            STEP_PROFILE_ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_enter_code)],

            # Запит карти за телефоном
            STEP_FIND_CARD_PHONE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_find_phone)],

            # Депозит
            STEP_CLIENT_CARD:        [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
            STEP_PROVIDER:           [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT:            [CallbackQueryHandler(process_payment)],
            STEP_DEPOSIT_AMOUNT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
            STEP_CONFIRM_FILE:       [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file)],
            STEP_CONFIRMATION:       [CallbackQueryHandler(confirm_submission)],

            # Виведення
            STEP_WITHDRAW_AMOUNT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
            STEP_WITHDRAW_METHOD:    [CallbackQueryHandler(process_withdraw_method)],
            STEP_WITHDRAW_DETAILS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
            STEP_WITHDRAW_CONFIRM:   [CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$")],

            # Реєстрація
            STEP_REG_NAME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            STEP_REG_PHONE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            STEP_REG_CODE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, register_code)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)

    # Хендлер для reply від адміна (усі теми)
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1,
    )


def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


# ——— Команда /start ——————————————————————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 КЛІЄНТ", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    markup = InlineKeyboardMarkup(keyboard)

    caption = "Вітаємо у *BIG GAME MONEY!* Оберіть дію:"
    if update.message:
        with open(GIF_PATH, "rb") as gif:
            await update.message.reply_animation(
                animation=gif,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup
            )
    else:
        await update.callback_query.answer()
        with open(GIF_PATH, "rb") as gif:
            await update.callback_query.message.reply_animation(
                animation=gif,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=markup
            )
    return STEP_MENU


# ——— Головне меню —————————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    is_admin = query.from_user.id == ADMIN_ID
    if not is_admin:
        try: await query.message.delete()
        except: pass

    data = query.data
    if data == "admin_panel":
        kb = [
            [InlineKeyboardButton("💰 Депозити", callback_data="admin_deposits")],
            [InlineKeyboardButton("👤 Користувачі", callback_data="admin_users")],
            [InlineKeyboardButton("📄 Виведення", callback_data="admin_withdrawals")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.reply_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    if data in ("client", "deposit", "withdraw", "register", "help"):
        return await client_menu_handler(update, context)

    # — Адмін-функції —
    if data == "admin_deposits":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, card, provider, payment, amount, timestamp FROM deposits ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = "Немає депозитів." if not rows else "\n\n".join(
            f"👤 {r[0]}\nКарта: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\nСума: {r[4]}\n🕒 {r[5]}"
            for r in rows
        )
        await query.message.reply_text(f"Останні депозити:\n\n{text}")
        return STEP_MENU

    if data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = "Немає користувачів." if not rows else "\n\n".join(
            f"👤 {r[0]}\n📞 {r[1]}\nСтатус: {r[2]}" for r in rows
        )
        await query.message.reply_text(f"Останні користувачі:\n\n{text}")
        return STEP_MENU

    if data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, amount, method, details, timestamp FROM withdrawals ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = "Немає заявок." if not rows else "\n\n".join(
            f"👤 {r[0]}\n💸 {r[1]}\nМетод: {r[2]}\nРеквізити: {r[3]}\n🕒 {r[4]}"
            for r in rows
        )
        await query.message.reply_text(f"Останні виведення:\n\n{text}")
        return STEP_MENU

    if data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            u = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            d = conn.execute("SELECT COUNT(*) FROM deposits").fetchone()[0]
            w = conn.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        await query.message.reply_text(f"📊 Статистика:\n👤 {u}\n💰 {d}\n📄 {w}")
        return STEP_MENU

    if data in ("back", "home"):
        return await start(update, context)

    await query.message.reply_text("Функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Підменю “КЛІЄНТ” —————————————————————————————
async def client_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try: await query.message.delete()
    except: pass

    keyboard = [
        [InlineKeyboardButton("💳 Мій профіль",             callback_data="client_profile")],
        [InlineKeyboardButton("📇 Дізнатися номер картки", callback_data="client_find_card")],
        [InlineKeyboardButton("💰 Поповнити",              callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",            callback_data="withdraw")],
        [InlineKeyboardButton("🏠 Головне меню",            callback_data="home")],
    ]
    await query.message.reply_text("Оберіть опцію:", reply_markup=InlineKeyboardMarkup(keyboard))

    data = query.data
    if data == "client_profile":
        await query.message.reply_text("Введіть номер картки (4–7 цифр):", reply_markup=nav_buttons())
        context.user_data["profile_mode"] = "direct"
        return STEP_PROFILE_ENTER_CARD
    if data == "client_find_card":
        await query.message.reply_text("Введіть телефон (10 цифр):", reply_markup=nav_buttons())
        context.user_data["profile_mode"] = "find"
        return STEP_PROFILE_ENTER_PHONE

    return STEP_CLIENT_MENU


# ——— “Мій профіль” – прямий ввод картки —————————————————
async def profile_enter_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,7}", card):
        await update.message.reply_text("4–7 цифр.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CARD
    context.user_data["profile_card"] = card
    await update.message.reply_text("Введіть телефон (10 цифр):", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_PHONE


# ——— “Мій профіль” – ввод телефону —————————————————————
async def profile_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"\d{10}", phone):
        await update.message.reply_text("10 цифр.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_PHONE

    mode = context.user_data.get("profile_mode")
    user_id = update.effective_user.id

    if mode == "direct":
        card = context.user_data["profile_card"]
        # Надсилаємо адміну на перевірку
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Авторизація клієнта – перевірити\nКартка: {card}\nТелефон: {phone}"
        )
        # Зберігаємо в clients
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO clients(user_id,phone,card,authorized) VALUES (?,?,?,1)",
                (user_id, phone, card)
            )
            conn.commit()
        await update.message.reply_text("Авторизовано ✅", reply_markup=nav_buttons())
        return STEP_CLIENT_MENU

    # режим "find"
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO clients(user_id,phone,authorized) VALUES (?,?,0)",
            (user_id, phone)
        )
        conn.commit()
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Хоче дізнатися свій номер картки\nТелефон: {phone}"
    )
    await update.message.reply_text("Введіть 4-значний код з SMS:", reply_markup=nav_buttons())
    return STEP_PROFILE_ENTER_CODE


# ——— “Мій профіль” – код підтвердження —————————————————
async def profile_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("4 цифри.", reply_markup=nav_buttons())
        return STEP_PROFILE_ENTER_CODE

    user_id = update.effective_user.id
    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код для клієнта {user_id}: {code}"
    )
    # Зберігаємо mapping для admin_reply
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id) VALUES (?,?)",
            (msg.message_id, user_id)
        )
        conn.commit()

    await update.message.reply_text("Код відправлено адміну. Чекайте…", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Reply-хендлер адміністратора —————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig_id = update.message.reply_to_message.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id FROM threads WHERE admin_msg_id = ?", (orig_id,)
        ).fetchone()
    if not row:
        await update.message.reply_text("Немає ланцюга.")
        return

    user_id = row[0]
    # Перевіряємо, чи це profile-код (authorized=0)
    with sqlite3.connect(DB_NAME) as conn:
        cl = conn.execute(
            "SELECT authorized FROM clients WHERE user_id = ?", (user_id,)
        ).fetchone()
    if cl and cl[0] == 0:
        card = update.message.text.strip()
        # Оновлюємо клієнта
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "UPDATE clients SET card=?, authorized=1 WHERE user_id=?",
                (card, user_id)
            )
            conn.commit()
        # Доставляємо клієнту картку
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Ваш номер картки: {card}\nАвторизація успішна ✅"
        )
        return

    # Інакше – звичайний reply
    await context.bot.send_message(chat_id=user_id, text=update.message.text)
    await update.message.reply_text("✅ Відправлено клієнту.")


# ——— Флоу Депозит —————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("4–5 цифр.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER


async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back","home"):
        return await client_menu_handler(update, context)
    context.user_data["provider"] = query.data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await query.message.reply_text("Метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back","home"):
        return await client_menu_handler(update, context)
    context.user_data["payment"] = query.data
    await query.message.reply_text("Введіть суму депозиту:", reply_markup=nav_buttons())
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
    await update.message.reply_text("Надішліть підтвердження (фото/документ/відео):", reply_markup=nav_buttons())
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
    query = update.callback_query; await query.answer()
    user     = query.from_user
    card     = context.user_data["card"]
    provider = context.user_data["provider"]
    payment  = context.user_data["payment"]
    amount   = context.user_data["deposit_amount"]
    file_msg: Message = context.user_data["file"]

    caption = (
        f"Депозит:\nКартка: {card}\nПровайдер: {provider}\n"
        f"Оплата: {payment}\nСума: {amount}"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, username TEXT,
                card TEXT, provider TEXT,
                payment TEXT, amount REAL,
                file_type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER
            )
        """)
        conn.commit()

    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id) VALUES (?,?)",
            (admin_msg.message_id, user.id)
        )
        conn.execute(
            "INSERT INTO deposits(user_id, username, card, provider, payment, amount, file_type) VALUES (?,?,?,?,?,?,?)",
            (user.id, user.username or "", card, provider, payment, amount,
             file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await query.message.reply_text("Депозит надіслано ✅", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу Виведення —————————————————————————————
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
    query = update.callback_query; await query.answer()
    method = query.data
    if method in ("back","home"):
        return await client_menu_handler(update, context)
    context.user_data["withdraw_method"] = method
    await query.message.reply_text("Введіть реквізити:", reply_markup=nav_buttons())
    return STEP_WITHDRAW_DETAILS


async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details
    amt = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    text = f"Підтвердити виведення?\nСума: {amt}\nМетод: {method}\nРеквізити: {details}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
    await update.message.reply_text(text, reply_markup=kb)
    return STEP_WITHDRAW_CONFIRM


async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = query.from_user
    amt = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    details = context.user_data["withdraw_details"]

    text = f"Виведення:\nСума: {amt}\nМетод: {method}\nРеквізити: {details}"
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, username TEXT,
                amount REAL, method TEXT,
                details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO withdrawals(user_id, username, amount, method, details) VALUES (?,?,?,?,?)",
            (user.id, user.username or "", amt, method, details)
        )
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id) VALUES (?,?)",
            (admin_msg.message_id, user.id)
        )
        conn.commit()

    await query.message.reply_text("Заявка на виведення надіслана ✅", reply_markup=nav_buttons())
    return STEP_CLIENT_MENU


# ——— Флоу Реєстрація —————————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть телефон (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний телефон.", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    name = context.user_data["reg_name"]
    user_id = update.effective_user.id

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація\nІм'я: {name}\nТелефон: {phone}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, name TEXT,
                phone TEXT, status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO registrations(user_id, name, phone) VALUES (?,?,?)",
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
    name = context.user_data["reg_name"]
    user_id = update.effective_user.id

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код реєстрації {code} від {name} ({user_id})"
    )
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id) VALUES (?,?)",
            (msg.message_id, user_id)
        )
        conn.commit()

    await update.message.reply_text("Код відправлено адміну. Чекайте підтвердження.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Хендлер reply для адміністратора —————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id FROM threads WHERE admin_msg_id = ?", (orig,)
        ).fetchone()
    if not row:
        await update.message.reply_text("Ланцюг не знайдено.")
        return
    user_id = row[0]
    # Якщо клієнт в процесі авторизації profile_find_phone
    with sqlite3.connect(DB_NAME) as conn:
        auth = conn.execute(
            "SELECT authorized FROM clients WHERE user_id = ?", (user_id,)
        ).fetchone()
    if auth and auth[0] == 0:
        card = update.message.text.strip()
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "UPDATE clients SET card=?, authorized=1 WHERE user_id=?",
                (card, user_id)
            )
            conn.commit()
        await context.bot.send_message(chat_id=user_id, text=f"Ваш номер картки: {card}\nАвторизація успішна ✅")
        return
    # Сюди default-reply (депозити / виведення / реєстрація)
    await context.bot.send_message(chat_id=user_id, text=update.message.text)
    await update.message.reply_text("✅ Доставлено.")
