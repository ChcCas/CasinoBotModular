import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME

# ——— Стани ——————————————————————————————————
(
    STEP_MENU,
    STEP_DEPOSIT_CHOICE,
    STEP_CLIENT_CHOICE,
    STEP_CLIENT_CARD,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CRYPTO_TYPE,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_WITHDRAW_CODE,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_DEST,
    STEP_WITHDRAW_CONFIRM,
    STEP_WITHDRAW_ACK,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
) = range(17)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Головне меню
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # “Поповнити” вибір
            STEP_DEPOSIT_CHOICE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(deposit_choice_handler),
            ],

            # “Клієнт” вибір
            STEP_CLIENT_CHOICE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(client_choice_handler),
            ],

            # Флоу поповнення карткою
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

            # Флоу виведення коштів
            STEP_WITHDRAW_CODE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_code),
            ],
            STEP_WITHDRAW_AMOUNT: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount),
            ],
            STEP_WITHDRAW_DEST: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_dest),
            ],
            STEP_WITHDRAW_CONFIRM: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(withdraw_confirm, pattern="^send_withdraw$")
            ],
            STEP_WITHDRAW_ACK: [
                CallbackQueryHandler(withdraw_ack, pattern="^ack_withdraw$")
            ],

            # Флоу «Реєстрація»
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

    # Адмін може reply на заявку
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1
    )


def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])


# ——— /start ——————————————————————————————————
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


# ——— Обробка головного меню ————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
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

    # Поповнити — вибір сценарію
    if data == "deposit":
        kb = [
            [InlineKeyboardButton("Як клієнт", callback_data="deposit_card")],
            [InlineKeyboardButton("Грати без картки", callback_data="no_card")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Як ви бажаєте поповнити баланс?", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_DEPOSIT_CHOICE

    # Вивід коштів — початок флоу
    if data == "withdraw":
        await query.message.edit_text(
            "Введіть код заявки (формат 00-00-00-00-00-00-00):",
            reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_CODE

    # Сценарій «Клієнт»
    if data == "client":
        kb = [
            [InlineKeyboardButton("Ввести номер картки", callback_data="enter_card")],
            [InlineKeyboardButton("Зняти кешбек", callback_data="withdraw_cashback")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Будь ласка, оберіть дію:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_CLIENT_CHOICE

    # Реєстрація
    if data == "register":
        await query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # Назад / Головне меню
    if data in ("back", "home"):
        return await start(update, context)

    # Інші — ще в розробці
    await query.message.edit_text("Ця функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Обробник “Поповнити” ——————————————————————
async def deposit_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    choice = query.data

    if choice == "deposit_card":
        await query.message.edit_text("Введіть номер картки для поповнення балансу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if choice == "no_card":
        kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [[
            InlineKeyboardButton("◀️ Назад", callback_data="back"),
            InlineKeyboardButton("🏠 Головне меню", callback_data="home")
        ]]
        await query.message.edit_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_PROVIDER


# ——— Обробник “Клієнт” ——————————————————————
async def client_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data

    if data == "enter_card":
        await query.message.edit_text("Введіть номер картки клієнта клубу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if data == "withdraw_cashback":
        await query.message.edit_text("Функція зняття кешбеку буде доступна найближчим часом.", reply_markup=nav_buttons())
        return STEP_MENU


# ——— Флоу поповнення ——————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат картки. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card

    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [[
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home")
    ]]
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
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
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    choice = query.data
    context.user_data["payment"] = choice

    if choice == "Карта":
        text = (
            "Переказуйте кошти на картку:\n\n"
            "Тарасюк Віталій\nОщадбанк\n4790 7299 5675 1465\n\n"
            "Після переказу надішліть підтвердження будь-яким форматом:\n"
            "– фото/скріншот\n– документ (PDF)\n– відео"
        )
        await query.message.edit_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE

    # Криптопереказ
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.edit_text("Оберіть метод криптопереказу:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE

async def process_crypto_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    choice = query.data
    context.user_data["payment"] = choice

    if choice == "Trustee Plus":
        text = (
            "Переказуйте USDT на акаунт Trustee Plus:\n\n"
            "ID: bgm001\n\n"
            "Після переказу надішліть підтвердження:\n"
            "– фото\n– документ\n– відео"
        )
        await query.message.edit_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE

    await query.message.edit_text(f"Метод «{choice}» в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Натисніть для підтвердження надсилання:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user
    card = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment = context.user_data.get("payment")
    file_msg: Message = context.user_data.get("file")

    caption = f"Заявка від клієнта:\nКартка: {card}\nПровайдер: {provider}\nМетод: {payment}"
    await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

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
            "INSERT INTO deposits (user_id, username, card, provider, payment, file_type) VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.username or "", card, provider, payment, file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await query.message.edit_text("✅ Поповнення надіслано.", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу виведення коштів ——————————————————————
async def withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r'(?:\d{2}-){6}\d{2}', code):
        await update.message.reply_text("Невірний формат коду. Використайте 00-00-00-00-00-00-00.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE
    context.user_data["withdraw_code"] = code
    await update.message.reply_text("Введіть суму виводу (мінімум 200):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 200:
        await update.message.reply_text("Некоректна сума. Вкажіть число від 200.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT
    context.user_data["withdraw_amount"] = text
    await update.message.reply_text(
        "Введіть реквізити для отримання:\n"
        "– для банківського переказу: 16-значний номер картки\n"
        "– для крипто: ваш ID або адресу", reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DEST

async def withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest = update.message.text.strip()
    # визначаємо тип
    method = 'card' if re.fullmatch(r'\d{16}', dest) else 'crypto'
    context.user_data["withdraw_method"] = method
    context.user_data["withdraw_dest"] = dest
    kb = [
        [InlineKeyboardButton("✅ Надіслати заявку", callback_data="send_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Перевірте дані та натисніть «Надіслати заявку»", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_CONFIRM

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user
    code = context.user_data["withdraw_code"]
    amount = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    dest = context.user_data["withdraw_dest"]

    # запис у БД
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
        conn.execute(
            "INSERT INTO withdrawals(user_id, username, amount, method, details, source_code) VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.username or "", amount, method, dest, code)
        )
        conn.commit()

    # повідомити адміну
    text = (
        f"🛎 Заявка на виведення:\n"
        f"Код: {code}\n"
        f"Сума: {amount}\n"
        f"Реквізити: {dest}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    # відповісти користувачу
    kb = [[InlineKeyboardButton("Підтверджую отримання", callback_data="ack_withdraw")]]
    await query.message.edit_text("✅ Заявка відправлена. Коли отримаєте переказ — натисніть кнопку нижче:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_ACK

async def withdraw_ack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user

    # повідомити адміну про підтвердження
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"✔️ Користувач @{user.username or user.id} підтвердив отримання коштів.")
    await query.message.edit_text("✅ Дякуємо за підтвердження!", reply_markup=nav_buttons())
    return STEP_MENU


# ——— Флоу «Реєстрація» ——————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть номер телефону (формат 0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний формат телефону. Спробуйте ще раз.", reply_markup=nav_buttons())
        return STEP_REG_PHONE

    context.user_data["reg_phone"] = phone
    name = context.user_data["reg_name"]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація:\n👤 {name}\n📞 {phone}")

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

    await update.message.reply_text("Дякуємо! Введіть 4-значний код підтвердження:", reply_markup=nav_buttons())
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


# ——— Обробка відповіді адміна ——————————————————————
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

    if provider == "🎰 SUPEROMATIC":
        note = (
            "Для початку гри перейдіть за посиланням:\n"
            "https://kod.greenhost.pw\n\n"
            "Якщо посилання не відкривається — увімкніть VPN.\n"
            "Більше інформації — у розділі «Допомога»."
        )
    else:  # provider == "🏆 CHAMPION"
        note = (
            "Дякуємо за вибір CHAMPION!\n\n"
            "Щоб розпочати гру, натисніть на іконку 🎰\n"
            "у лівому верхньому кутку екрану бота та введіть код."
        )

    final_text = f"{admin_text}\n\n{note}"
    await context.bot.send_message(chat_id=user_id, text=final_text)
    await update.message.reply_text("✅ Відповідь доставлено.")
