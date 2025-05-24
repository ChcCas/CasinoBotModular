import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME

# ——— Стани ———————————————————————————————
(
    STEP_MENU,
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CRYPTO_TYPE,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
) = range(10)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Головне меню
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # Флоу “Я Клієнт”
            STEP_CLIENT_CARD: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card),
            ],
            STEP_PROVIDER: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(process_provider),
            ],
            STEP_PAYMENT: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(process_payment),
            ],
            STEP_CRYPTO_TYPE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(process_crypto_choice),
            ],
            STEP_CONFIRM_FILE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file),
            ],
            STEP_CONFIRMATION: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(confirm_submission, pattern="^confirm$")
            ],

            # Флоу “Реєстрація”
            STEP_REG_NAME: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
            ],
            STEP_REG_PHONE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
            ],
            STEP_REG_CODE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)

    # Адмін може reply прямо у боті
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY,
            admin_reply
        ),
        group=1
    )


def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Клієнт", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")],
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    text = "BIG BAME MONEY"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
        await query.message.edit_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    # Admin deposits
    if data == "admin_deposits":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT username, card, provider, payment, timestamp FROM deposits "
                "ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()
        text = "Записів не знайдено." if not rows else "\n\n".join(
            f"👤 {r[0] or '—'}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\n🕒 {r[4]}"
            for r in rows
        )
        await query.message.edit_text(f"Останні поповнення:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Admin users
    if data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = "Немає зареєстрованих користувачів." if not rows else "\n\n".join(
            f"👤 Ім’я: {r[0]}\n📞 Телефон: {r[1]}\nСтатус: {r[2]}"
            for r in rows
        )
        await query.message.edit_text(f"Останні користувачі:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Admin withdrawals
    if data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    amount TEXT,
                    method TEXT,
                    details TEXT,
                    source_code TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            rows = conn.execute(
                "SELECT username, amount, method, details, source_code, timestamp "
                "FROM withdrawals ORDER BY id DESC LIMIT 10"
            ).fetchall()
        text = "Заявок на виведення немає." if not rows else "\n\n".join(
            f"👤 {r[0] or '—'}\n💸 Сума: {r[1]}\n💳 Метод: {r[2]}\n📥 Реквізити: {r[3]}\n🔢 Код: {r[4]}\n🕒 {r[5]}"
            for r in rows
        )
        await query.message.edit_text(f"Останні заявки на виведення:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Admin stats
    if data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            users = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
            deps  = conn.execute("SELECT COUNT(*) FROM deposits").fetchone()[0]
            wds   = conn.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
        stats = f"📊 Статистика:\n👤 Користувачів: {users}\n💰 Поповнень: {deps}\n📄 Виведень: {wds}"
        await query.message.edit_text(stats, reply_markup=nav_buttons())
        return STEP_MENU

    # Я Клієнт
    if data == "client":
        await query.message.edit_text("Введіть номер картки клієнта клубу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    # Реєстрація
    if data == "register":
        await query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # Назад / Головне меню
    if data in ("back", "home"):
        return await start(update, context)

    # Інше
    await query.message.edit_text("Ця функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU


async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат. Введіть коректний номер картки.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [[
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ]]
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER


async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    context.user_data["provider"] = query.data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS] + [[
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ]]
    await query.message.edit_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    data = query.data
    context.user_data["payment"] = data

    if data == "Карта":
        text = (
            "Будь ласка, зробіть переказ на карту:\n\n"
            "Тарасюк Віталій\nОщадбанк\n4790 7299 5675 1465\n\n"
            "Після переказу надшліть підтвердження будь-яким із форматів:\n"
            "– фото\n– документ\n– відео"
        )
        await query.message.edit_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE

    # Криптопереказ
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home")
        ]
    ]
    await query.message.edit_text("Оберіть метод криптопереказу:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE


async def process_crypto_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    choice = query.data
    context.user_data["payment"] = choice

    if choice == "Trustee Plus":
        text = (
            "Зробіть переказ у USDT на:\n\n"
            "ID: bgm001\nПримітка: приймаємо тільки USDT\n\n"
            "Після переказу надшліть підтвердження будь-яким із форматів:\n"
            "– фото\n– документ\n– відео"
        )
        await query.message.edit_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE

    await query.message.edit_text(
        f"Метод «{choice}» наразі в розробці. Оберіть інший спосіб.",
        reply_markup=nav_buttons()
    )
    return STEP_MENU


async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home")
        ]
    ]
    await update.message.reply_text("Натисніть для підтвердження надсилання:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION


async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    card = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    file_msg: Message = context.user_data.get("file")

    caption = (
        f"Заявка від клієнта:\n"
        f"Картка: {card}\nПровайдер: {provider}\nМетод оплати: {payment}"
    )

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER,
                user_msg_id   INTEGER,
                provider      TEXT
            )
        """)
        conn.commit()

    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id, user_msg_id, provider) VALUES (?, ?, ?, ?)",
            (admin_msg.message_id, user.id, file_msg.message_id, provider)
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
            (user.id, user.username or "", card, provider, payment,
             file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await query.message.edit_text("Дякую! Вашу заявку надіслано.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу “Реєстрація” ——————————————————————
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
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація:\n👤 Ім'я: {name}\n📞 Телефон: {phone}")

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

    await update.message.reply_text("Дякуємо! Чекайте код підтверження. Введіть 4-значний код:", reply_markup=nav_buttons())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код. Введіть 4 цифри:", reply_markup=nav_buttons())
        return STEP_REG_CODE

    name = context.user_data["reg_name"]
    user = update.effective_user
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Код підтвердження від {name} ({user.id}): {code}")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])
    await update.message.reply_text("Реєстрацію успішно надіслано!", reply_markup=kb)
    return STEP_MENU


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    admin_msg_id = orig.message_id

    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id, provider FROM threads WHERE admin_msg_id = ?",
            (admin_msg_id,)
        ).fetchone()

    if not row:
        await update.message.reply_text("❌ Не вдалося знайти користувача для відповіді.")
        return

    user_id, provider = row
    admin_text = update.message.text.strip()
    code_line = "00-00-00-00-00-00-00"

    if provider == "🎰 SUPEROMATIC":
        note = (
            'Для гри перейдіть за посиланням "https://kod.greenhost.pw", '
            'якщо посилання не відкривається, увімкніть VPN. '
            'Інші питання шукайте у розділі "Допомога".'
        )
    else:  # provider == "🏆 CHAMPION"
        note = (
            'Дякуємо за ваш вибір! Для початку гри відкрийте вікно 🎰 '
            'у лівому куті екрану бота та введіть отриманий код.'
        )

    final_text = f"{admin_text}\n\n{code_line}\n\n{note}"
    await context.bot.send_message(chat_id=user_id, text=final_text)
    await update.message.reply_text("✅ Відповідь доставлено.")
