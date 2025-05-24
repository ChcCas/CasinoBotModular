import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME


# === Стан ===
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
) = range(9)


PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
       states={
    STEP_MENU: [CallbackQueryHandler(menu_handler)],
    # … ваші існуючі стани …
    STEP_CONFIRMATION: [CallbackQueryHandler(confirm_submission)],

    # Ось сюди вставляємо:
    STEP_REG_NAME: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
        CallbackQueryHandler(menu_handler, pattern="^(back|home)$")
    ],
    STEP_REG_PHONE: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
        CallbackQueryHandler(menu_handler, pattern="^(back|home)$")
    ],
    STEP_REG_CODE: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),
        CallbackQueryHandler(menu_handler, pattern="^(back|home)$")
    ],
},

            STEP_MENU: [CallbackQueryHandler(menu_handler)],
            STEP_CLIENT_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
            STEP_PROVIDER: [CallbackQueryHandler(process_provider)],
            STEP_PAYMENT: [CallbackQueryHandler(process_payment)],
            STEP_CONFIRM_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file)],
            STEP_CONFIRMATION: [CallbackQueryHandler(confirm_submission)],
        },async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["reg_name"] = name
    await update.message.reply_text(
        "Введіть номер телефону (формат: 0XXXXXXXXX):",
        reply_markup=nav_buttons()
    )
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text(
            "Невірний формат телефону. Спробуйте ще раз.",
            reply_markup=nav_buttons()
        )
        return STEP_REG_PHONE

    context.user_data["reg_phone"] = phone

    # Пересилка адміну
    name = context.user_data["reg_name"]
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Нова реєстрація:\n👤 Ім'я: {name}\n📞 Телефон: {phone}"
    )

    # Запис у БД
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                status TEXT DEFAULT 'pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute(
            "INSERT INTO registrations (user_id, name, phone) VALUES (?, ?, ?)",
            (update.effective_user.id, name, phone)
        )
        conn.commit()

    await update.message.reply_text(
        "Дякуємо! Чекайте код підтвердження. Введіть 4-значний код:",
        reply_markup=nav_buttons()
    )
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text(
            "Невірний код. Введіть, будь ласка, 4 цифри:",
            reply_markup=nav_buttons()
        )
        return STEP_REG_CODE

    # Пересилка адміну коду
    name = context.user_data["reg_name"]
    user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код підтвердження від {name} ({user.id}): {code}"
    )

    # Від клієнта — кнопка “Поповнити”
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])
    await update.message.reply_text(
        "Реєстрацію успішно надіслано!",
        reply_markup=keyboard
    )
    return STEP_MENU

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
            text = "\n\n".join([
                f"👤 {r[0] or '—'}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\n🕒 {r[4]}"
                for r in rows
            ])
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
            text = "\n\n".join([
                f"👤 Ім’я: {r[0]}\n📞 Телефон: {r[1]}\nСтатус: {r[2]}"
                for r in rows
            ])
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
            text = "\n\n".join([
                f"👤 {r[0] or '—'}\n💸 Сума: {r[1]}\n💳 Метод: {r[2]}\n📥 Реквізити: {r[3]}\n🔢 Код: {r[4]}\n🕒 {r[5]}"
                for r in rows
            ])
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

async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат. Введіть коректний номер картки.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    context.user_data["card"] = card

    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ])
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data in ("back", "home"):
        return await menu_handler(update, context)

    context.user_data["provider"] = data
    keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ])
    await query.message.reply_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data in ("back", "home"):
        return await menu_handler(update, context)

    context.user_data["payment"] = data
    await query.message.reply_text(
        "Завантажте файл підтвердження (фото/документ/відео):",
        reply_markup=nav_buttons()
    )
    return STEP_CONFIRM_FILE

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    keyboard = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.message.reply_text("Натисніть для підтвердження надсилання:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    card = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    file_msg: Message = context.user_data.get("file")

    text = f"Заявка від клієнта:\nКартка: {card}\nПровайдер: {provider}\nМетод оплати: {payment}"
    await file_msg.copy_to(chat_id=ADMIN_ID, caption=text)

    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            card TEXT,
            provider TEXT,
            payment TEXT,
            file_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""INSERT INTO deposits (user_id, username, card, provider, payment, file_type)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user.id, user.username or '', card, provider, payment, file_msg.effective_attachment.__class__.__name__))
        conn.commit()

    await query.message.reply_text("Дякуємо! Вашу заявку надіслано.", reply_markup=nav_buttons())
    return STEP_MENU
