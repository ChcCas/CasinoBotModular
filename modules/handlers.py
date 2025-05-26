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
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
) = range(13)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]


def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # Флоу “КЛІЄНТ”
            STEP_CLIENT_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_PROVIDER: [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT: [CallbackQueryHandler(process_payment)],
            STEP_CONFIRM_FILE: [
                MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file)
            ],
            STEP_CONFIRMATION: [CallbackQueryHandler(confirm_submission)],

            # Флоу “Реєстрація”
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

            # Флоу “Виведення”
            STEP_WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_METHOD: [
                CallbackQueryHandler(process_withdraw_method),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
            STEP_WITHDRAW_CONFIRM: [
                CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$"),
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)

    # Хендлер для reply від адміністратора
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

    caption = "Вітаємо у BIG GAME MONEY! Оберіть дію:"

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


# ——— Обробка меню —————————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    is_admin = query.from_user.id == ADMIN_ID

    # Звичайному користувачу видаляємо попереднє меню
    if not is_admin:
        try:
            await query.message.delete()
        except:
            pass

    data = query.data

    # Адмін-панель
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

    # КЛІЄНТ
    if data == "client":
        await query.message.reply_text(
            "Введіть номер картки клієнта клубу:", reply_markup=nav_buttons()
        )
        return STEP_CLIENT_CARD

    # Реєстрація
    if data == "register":
        await query.message.reply_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # Поповнити
    if data == "deposit":
        await query.message.reply_text(
            "Введіть номер картки клієнта клубу:", reply_markup=nav_buttons()
        )
        return STEP_CLIENT_CARD

    # Виведення
    if data == "withdraw":
        await query.message.reply_text("Введіть суму для виведення:", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    # Допомога
    if data == "help":
        await query.message.reply_text(
            "💡 Інструкція:\n"
            "• 🎲 «КЛІЄНТ» – перегляд балансу (у розробці)\n"
            "• 💰 «Поповнити» – поповнення рахунку\n"
            "• 💸 «Вивід коштів» – зняття коштів\n"
            "• 📝 «Реєстрація» – створити акаунт\n",
            reply_markup=nav_buttons(),
        )
        return STEP_MENU

    # Назад / Головне меню
    if data in ("back", "home"):
        return await start(update, context)

    # Адмін-запити
    if data == "admin_deposits":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, card, provider, payment, timestamp FROM deposits "
                "ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = (
            "Записів не знайдено."
            if not rows
            else "\n\n".join(
                f"👤 {r[0] or '—'}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\n🕒 {r[4]}"
                for r in rows
            )
        )
        await query.message.reply_text(f"Останні поповнення:\n\n{text}")
        return STEP_MENU

    if data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = (
            "Немає зареєстрованих користувачів."
            if not rows
            else "\n\n".join(
                f"👤 Ім’я: {r[0]}\n📞 Телефон: {r[1]}\nСтатус: {r[2]}" for r in rows
            )
        )
        await query.message.reply_text(f"Останні користувачі:\n\n{text}")
        return STEP_MENU

    if data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, amount, method, details, source_code, timestamp FROM withdrawals "
                "ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = (
            "Заявок немає."
            if not rows
            else "\n\n".join(
                f"👤 {r[0] or '—'}\n💸 Сума: {r[1]}\nМетод: {r[2]}\n📥 {r[3]}\n🔢 {r[4]}\n🕒 {r[5]}"
                for r in rows
            )
        )
        await query.message.reply_text(f"Останні заявки на виведення:\n\n{text}")
        return STEP_MENU

    if data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            users = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            deps = conn.execute("SELECT COUNT(*) FROM deposits").fetchone()[0]
            wds = conn.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        await query.message.reply_text(
            f"📊 Статистика:\n👤 Користувачів: {users}\n💰 Поповнень: {deps}\n📄 Виведень: {wds}"
        )
        return STEP_MENU

    # За замовчуванням
    await query.message.reply_text("Ця функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу “КЛІЄНТ” —————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат. Введіть 4–5 цифр.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append(
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
        ]
    )
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)

    context.user_data["provider"] = query.data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append(
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
        ]
    )
    await query.message.reply_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)

    context.user_data["payment"] = query.data
    await query.message.reply_text("Завантажте підтвердження (документ/фото/відео):", reply_markup=nav_buttons())
    return STEP_CONFIRM_FILE

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
        ],
    ]
    await update.message.reply_text("Натисніть для підтвердження:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user
    card = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    file_msg: Message = context.user_data.get("file")

    caption = f"Заявка від клієнта:\nКартка: {card}\nПровайдер: {provider}\nМетод: {payment}"

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                user_msg_id INTEGER
            )
        """)
        conn.commit()

    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id, user_msg_id) VALUES (?, ?, ?)",
            (admin_msg.message_id, user.id, file_msg.message_id),
        )
        conn.commit()

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                card TEXT,
                provider TEXT,
                payment TEXT,
                file_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO deposits(user_id, username, card, provider, payment, file_type) VALUES (?, ?, ?, ?, ?, ?)",
            (
                user.id,
                user.username or "",
                card,
                provider,
                payment,
                file_msg.effective_attachment.__class__.__name__,
            ),
        )
        conn.commit()

    await query.message.reply_text("Дякуємо! Вашу заявку надіслано.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу “Виведення” —————————————————————————————
async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", amount):
        await update.message.reply_text("Невірний формат суми. Введіть число.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amount
    keyboard = [[InlineKeyboardButton(m, callback_data=m)] for m in PAYMENTS]
    keyboard.append(
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
        ]
    )
    await update.message.reply_text("Оберіть метод виведення:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    method = query.data
    context.user_data["withdraw_method"] = method
    await query.message.reply_text("Введіть реквізити для виведення:", reply_markup=nav_buttons())
    return STEP_WITHDRAW_DETAILS

async def process_withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details
    text = (
        f"Підтверджуєте виведення?\n"
        f"💸 Сума: {context.user_data['withdraw_amount']}\n"
        f"💳 Метод: {context.user_data['withdraw_method']}\n"
        f"📥 Реквізити: {details}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])
    await update.message.reply_text(text, reply_markup=kb)
    return STEP_WITHDRAW_CONFIRM

async def confirm_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = query.from_user
    amt = context.user_data.get("withdraw_amount")
    method = context.user_data.get("withdraw_method")
    details = context.user_data.get("withdraw_details")

    text = (
        f"Заявка на виведення:\n"
        f"Сума: {amt}\n"
        f"Метод: {method}\n"
        f"Реквізити: {details}"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount TEXT,
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

    await query.message.reply_text("Ваша заявка на виведення надіслана адміну.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу “Реєстрація” ———————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть номер телефону (формат: 0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний формат телефону. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_REG_PHONE

    context.user_data["reg_phone"] = phone
    name = context.user_data["reg_name"]

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація:\n👤 Ім’я: {name}\n📞 Телефон: {phone}")

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
        conn.execute("INSERT INTO registrations(user_id, name, phone) VALUES (?, ?, ?)", (update.effective_user.id, name, phone))
        conn.commit()

    await update.message.reply_text("Дякуємо! Чекайте код підтвердження. Введіть 4-значний код:", reply_markup=nav_buttons())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код. Введіть 4 цифри:", reply_markup=nav_buttons())
        return STEP_REG_CODE

    name = context.user_data["reg_name"]
    user = update.effective_user

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Код підтвердження від {name} ({user.id}): {code}")

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
                               [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]])
    await update.message.reply_text("Реєстрацію успішно надіслано!", reply_markup=kb)
    return STEP_MENU


# ——— Хендлер відповіді адміна —————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    admin_msg_id = orig.message_id

    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id FROM threads WHERE admin_msg_id = ?", (admin_msg_id,)).fetchone()

    if not row:
        await update.message.reply_text("❌ Не вдалося знайти користувача для відповіді.")
        return

    user_id = row[0]
    await context.bot.send_message(chat_id=user_id, text=update.message.text)
    await update.message.reply_text("✅ Відповідь доставлено.")
