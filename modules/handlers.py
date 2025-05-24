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
    STEP_ADMIN_BROADCAST_MESSAGE,
    STEP_ADMIN_SEARCH_PROMPT,
    STEP_USER_HISTORY,
) = range(20)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={

            # Головне меню
            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            # Сценарії “Поповнити”
            STEP_DEPOSIT_CHOICE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(deposit_choice_handler),
            ],

            # Сценарії “Я клієнт”
            STEP_CLIENT_CHOICE: [
                CallbackQueryHandler(menu_handler, pattern="^(back|home)$"),
                CallbackQueryHandler(client_choice_handler),
            ],

            # Флоу поповнення
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

            # Флоу “Вивід коштів”
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

            # Адмін: розсилка та пошук
            STEP_ADMIN_BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)
            ],
            STEP_ADMIN_SEARCH_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_execute)
            ],

            # Особиста історія
            STEP_USER_HISTORY: [
                CallbackQueryHandler(user_history, pattern="^history$")
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

# — /start ——————————————————————————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎲 Клієнт",       callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація",   callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Історія",      callback_data="history")],
        [InlineKeyboardButton("ℹ️ Допомога",     callback_data="help")],
    ]
    if update.effective_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    text = "BIG BAME MONEY"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_MENU

# — Обробник головного меню та адмін-панелі ——————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = query.data

    # Адмін-панель
    if d == "admin_panel":
        kb = [
            [InlineKeyboardButton("👤 Історія реєстрацій", callback_data="admin_history_reg")],
            [InlineKeyboardButton("💰 Історія поповнень",  callback_data="admin_history_dep")],
            [InlineKeyboardButton("💸 Історія виведень",    callback_data="admin_history_wd")],
            [InlineKeyboardButton("✉️ Розсилка",           callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔍 Пошук користувача",   callback_data="admin_search")],
            [InlineKeyboardButton("🏠 Головне меню",        callback_data="home")],
        ]
        await query.message.edit_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    # Особиста історія клієнта
    if d == "history":
        return await user_history(update, context)

    # Адмін: Історія реєстрацій
    if d == "admin_history_reg":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT id, user_id, name, phone, status, timestamp "
                "FROM registrations ORDER BY timestamp DESC"
            ).fetchall()
        text = "Немає реєстрацій." if not rows else "\n\n".join(
            f"#{r[0]}  uid:{r[1]}  {r[2]}  {r[3]}  [{r[4]}]  {r[5]}" for r in rows
        )
        await query.message.edit_text(f"Історія реєстрацій:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Адмін: Історія поповнень
    if d == "admin_history_dep":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT id, user_id, username, card, provider, payment, timestamp "
                "FROM deposits ORDER BY timestamp DESC"
            ).fetchall()
        text = "Немає поповнень." if not rows else "\n\n".join(
            f"#{r[0]}  uid:{r[1]}  {r[2]}  картка:{r[3]}  провайдер:{r[4]}  спосіб:{r[5]}  {r[6]}"
            for r in rows
        )
        await query.message.edit_text(f"Історія поповнень:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Адмін: Історія виведень
    if d == "admin_history_wd":
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                "SELECT id, user_id, username, amount, method, details, source_code, timestamp "
                "FROM withdrawals ORDER BY timestamp DESC"
            ).fetchall()
        text = "Немає виведень." if not rows else "\n\n".join(
            f"#{r[0]}  uid:{r[1]}  {r[2]}  сума:{r[3]}  {r[4]}  {r[5]}  код:{r[6]}  {r[7]}"
            for r in rows
        )
        await query.message.edit_text(f"Історія виведень:\n\n{text}", reply_markup=nav_buttons())
        return STEP_MENU

    # Адмін: Розсилка
    if d == "admin_broadcast":
        await query.message.edit_text("Введіть текст для розсилки всім користувачам:", reply_markup=nav_buttons())
        return STEP_ADMIN_BROADCAST_MESSAGE

    # Адмін: Пошук користувача
    if d == "admin_search":
        await query.message.edit_text("Введіть user_id чи username для пошуку:", reply_markup=nav_buttons())
        return STEP_ADMIN_SEARCH_PROMPT

    # Поповнити → вибір сценарію
    if d == "deposit":
        kb = [
            [InlineKeyboardButton("Як клієнт",       callback_data="deposit_card")],
            [InlineKeyboardButton("Грати без картки", callback_data="no_card")],
            [InlineKeyboardButton("◀️ Назад",         callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Як бажаєте поповнити?", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_DEPOSIT_CHOICE

    # Виведення коштів
    if d == "withdraw":
        await query.message.edit_text("Введіть код заявки (00-00-00-00-00-00-00):", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE

    # Я клієнт → вибір дій
    if d == "client":
        kb = [
            [InlineKeyboardButton("Ввести номер картки", callback_data="enter_card")],
            [InlineKeyboardButton("Зняти кешбек",       callback_data="withdraw_cashback")],
            [InlineKeyboardButton("◀️ Назад",            callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню",    callback_data="home")],
        ]
        await query.message.edit_text("Оберіть дію:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_CLIENT_CHOICE

    # Реєстрація
    if d == "register":
        await query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # Назад або Головне меню
    if d in ("back", "home"):
        return await start(update, context)

    # Інші кнопки
    await query.message.edit_text("Ця функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

# — Особиста історія клієнта ——————————————————————————
async def user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    with sqlite3.connect(DB_NAME) as conn:
        deps = conn.execute(
            "SELECT card, provider, payment, timestamp "
            "FROM deposits WHERE user_id=? ORDER BY timestamp DESC",
            (uid,)
        ).fetchall()
        wds = conn.execute(
            "SELECT amount, method, details, source_code, timestamp "
            "FROM withdrawals WHERE user_id=? ORDER BY timestamp DESC",
            (uid,)
        ).fetchall()
        ths = conn.execute(
            "SELECT admin_msg_id, user_msg_id, provider "
            "FROM threads WHERE user_id=? ORDER BY admin_msg_id DESC",
            (uid,)
        ).fetchall()

    deps_text = "\n".join(
        f"• {r[3]} — {r[1]} / {r[2]} / картка {r[0]}" for r in deps
    ) or "немає поповнень."

    wds_text = "\n".join(
        f"• {r[4]} — {r[1]} / {r[2]} / {r[3]}" for r in wds
    ) or "немає виведень."

    ths_text = "\n".join(
        f"• admin_msg_id={r[0]} ↔ user_msg_id={r[1]} (provider={r[2]})" for r in ths
    ) or "немає історії повідомлень."

    text = (
        "📜 Ваша особиста історія\n\n"
        f"🔹 Поповнення:\n{deps_text}\n\n"
        f"🔸 Виведення:\n{wds_text}\n\n"
        f"💬 Повідомлення:\n{ths_text}"
    )
    await query.message.edit_text(text, reply_markup=nav_buttons())
    return STEP_MENU

# — Сценарій “Поповнити” ——————————————————————————
async def deposit_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "deposit_card":
        await query.message.edit_text("Введіть номер картки для поповнення:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    # роль “no_card” спрямовує відразу до вибору провайдера
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [[
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ]]
    await query.message.edit_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

# — Сценарій “Я клієнт” ——————————————————————————
async def client_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "enter_card":
        await query.message.edit_text("Введіть номер картки клієнта клубу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    await query.message.edit_text("Функція зняття кешбеку буде доступна пізніше.", reply_markup=nav_buttons())
    return STEP_MENU

# — Флоу поповнення ——————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат картки.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [[
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
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
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ]]
    await query.message.reply_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice in ("back", "home"):
        return await menu_handler(update, context)
    context.user_data["payment"] = choice

    if choice == "Карта":
        text = (
            "Переказуйте кошти на картку:\n\n"
            "Тарасюк Віталій\nОщадбанк\n4790 7299 5675 1465\n\n"
            "Після переказу надшліть підтвердження:\n"
            "– фото/скріншот\n– документ (PDF)\n– відео"
        )
        await query.message.edit_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE

    # крипто
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.edit_text("Оберіть метод криптопереказу:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE

async def process_crypto_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice in ("back", "home"):
        return await menu_handler(update, context)
    context.user_data["payment"] = choice
    if choice == "Trustee Plus":
        text = (
            "Переказуйте USDT на акаунт Trustee Plus:\n\n"
            "ID: bgm001\n\n"
            "Після переказу надшліть підтвердження:\n"
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
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Натисніть для підтвердження надсилання:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION

# — Оновлений confirm_submission ———————————————————
async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user     = update.effective_user
    card     = context.user_data.get("card")
    provider = context.user_data.get("provider", "—")
    payment  = context.user_data.get("payment", "—")
    file_msg: Message = context.user_data.get("file")

    # Формуємо caption
    lines = ["Нова заявка від клієнта:"]
    if card:
        lines.append(f"• Картка: {card}")
    lines.append(f"• Провайдер: {provider}")
    lines.append(f"• Метод: {payment}")
    caption = "\n".join(lines)

    # Підготовка таблиць
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                admin_msg_id INTEGER PRIMARY KEY,
                user_id       INTEGER,
                user_msg_id   INTEGER,
                provider      TEXT
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
                file_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    # Копіюємо файл адміну
    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)

    # Зберігаємо записи
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id,user_msg_id,provider) VALUES (?,?,?,?)",
            (admin_msg.message_id, user.id, file_msg.message_id, provider)
        )
        conn.execute(
            "INSERT INTO deposits(user_id,username,card,provider,payment,file_type) VALUES (?,?,?,?,?,?)",
            (
                user.id,
                user.username or "",
                card or "",
                provider,
                payment,
                file_msg.effective_attachment.__class__.__name__
            )
        )
        conn.commit()

    await query.message.edit_text("✅ Дякуємо! Ваша заявка надіслана.", reply_markup=nav_buttons())
    return STEP_MENU

# — Флоу виведення коштів ——————————————————————
async def withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r'(?:\d{2}-){6}\d{2}', code):
        await update.message.reply_text("Невірний формат коду.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE
    context.user_data["withdraw_code"] = code
    await update.message.reply_text("Введіть суму виводу (мінімум 200):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = update.message.text.strip()
    if not amt.isdigit() or int(amt) < 200:
        await update.message.reply_text("Некоректна сума.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT
    context.user_data["withdraw_amount"] = amt
    await update.message.reply_text(
        "Введіть реквізити:\n– 16 цифр картки\n– або крипто-адресу",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DEST

async def withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest = update.message.text.strip()
    method = 'card' if re.fullmatch(r'\d{16}', dest) else 'crypto'
    context.user_data["withdraw_method"] = method
    context.user_data["withdraw_dest"]   = dest
    kb = [
        [InlineKeyboardButton("✅ Надіслати заявку", callback_data="send_withdraw")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Перевірте дані й натисніть «Надіслати заявку»", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_CONFIRM

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user   = update.effective_user
    code   = context.user_data["withdraw_code"]
    amount = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    dest   = context.user_data["withdraw_dest"]

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
            "INSERT INTO withdrawals(user_id,username,amount,method,details,source_code) VALUES (?,?,?,?,?,?)",
            (user.id, user.username or "", amount, method, dest, code)
        )
        conn.commit()

    notify = (
        f"🛎 Заявка на виведення:\n"
        f"Код: {code}\nСума: {amount}\nРеквізити: {dest}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=notify)

    kb = [[InlineKeyboardButton("Підтверджую отримання", callback_data="ack_withdraw")]]
    await query.message.edit_text("✅ Заявка відправлена. Після отримання натисніть:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_ACK

async def withdraw_ack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"✔️ @{user.username or user.id} підтвердив отримання коштів."
    )
    await query.message.edit_text("✅ Дякуємо за підтвердження!", reply_markup=nav_buttons())
    return STEP_MENU

# — Флоу реєстрації ——————————————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний формат телефону.", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    context.user_data["reg_phone"] = phone
    name = context.user_data["reg_name"]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація: {name} | {phone}")
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
        conn.execute(
            "INSERT INTO registrations(user_id,name,phone) VALUES (?,?,?)",
            (update.effective_user.id, name, phone)
        )
        conn.commit()
    await update.message.reply_text("Введіть 4-значний код підтвердження:", reply_markup=nav_buttons())
    return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r"\d{4}", code):
        await update.message.reply_text("Невірний код.", reply_markup=nav_buttons())
        return STEP_REG_CODE
    name = context.user_data["reg_name"]
    user = update.effective_user
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Код підтвердження від {name} ({user.id}): {code}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ])
    await update.message.reply_text("Реєстрацію надіслано!", reply_markup=kb)
    return STEP_MENU

# — Адмін: розсилка ——————————————————————————
async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    with sqlite3.connect(DB_NAME) as conn:
        users = conn.execute("SELECT DISTINCT user_id FROM registrations").fetchall()
    for (uid,) in users:
        try:
            await context.bot.send_message(chat_id=uid, text=txt)
        except:
            pass
    await update.message.reply_text("✅ Розсилка виконана.", reply_markup=nav_buttons())
    return STEP_MENU

# — Адмін: пошук користувача ——————————————————————
async def admin_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    param = update.message.text.strip()
    uid = int(param) if param.isdigit() else None
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        if uid:
            regs = cur.execute(
                "SELECT id,user_id,name,phone,status,timestamp FROM registrations WHERE user_id=?",
                (uid,)
            ).fetchall()
            deps = cur.execute(
                "SELECT id,user_id,username,card,provider,payment,timestamp FROM deposits WHERE user_id=?",
                (uid,)
            ).fetchall()
            wds = cur.execute(
                "SELECT id,user_id,username,amount,method,details,source_code,timestamp FROM withdrawals WHERE user_id=?",
                (uid,)
            ).fetchall()
            ths = cur.execute(
                "SELECT admin_msg_id,user_msg_id,provider FROM threads WHERE user_id=?",
                (uid,)
            ).fetchall()
            hdr = f"Результати для user_id={uid}"
        else:
            regs = cur.execute(
                "SELECT id,user_id,name,phone,status,timestamp FROM registrations WHERE name LIKE ?",
                (f"%{param}%",)
            ).fetchall()
            deps = cur.execute(
                "SELECT id,user_id,username,card,provider,payment,timestamp FROM deposits WHERE username LIKE ?",
                (f"%{param}%",)
            ).fetchall()
            wds = cur.execute(
                "SELECT id,user_id,username,amount,method,details,source_code,timestamp FROM withdrawals WHERE username LIKE ?",
                (f"%{param}%",)
            ).fetchall()
            ths = cur.execute(
                "SELECT admin_msg_id,user_msg_id,provider FROM threads WHERE user_id IN (SELECT user_id FROM registrations WHERE name LIKE ?)",
                (f"%{param}%",)
            ).fetchall()
            hdr = f"Результати для '{param}'"

    sections = [f"🔎 {hdr}"]
    sections.append("Реєстрації:\n" + ( "\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|[{r[4]}]|{r[5]}" for r in regs) if regs else "немає"))
    sections.append("Поповнення:\n" + ( "\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}" for r in deps) if deps else "немає"))
    sections.append("Виведення:\n" + ( "\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|{r[4]}|{r[5]}|код:{r[6]}|{r[7]}" for r in wds) if wds else "немає"))
    sections.append("Повідомлення:\n" + ( "\n".join(f"admin_msg_id={r[0]} ↔ user_msg_id={r[1]} (prov={r[2]})" for r in ths) if ths else "немає"))

    await update.message.reply_text("\n\n".join(sections), reply_markup=nav_buttons())
    return STEP_MENU

# — Адмін: відповідь на заявку ——————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    admin_msg_id = orig.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id, provider FROM threads WHERE admin_msg_id=?",
            (admin_msg_id,)
        ).fetchone()
    if not row:
        await update.message.reply_text("❌ Користувача не знайдено.")
        return
    user_id, provider = row
    admin_txt = update.message.text.strip()

    if provider == "🏆 CHAMPION":
        note = (
            "Дякуємо за CHAMPION!\n"
            "Для гри натисніть на 🎰 в лівому нижньому куті бота."
        )
    else:
        note = (
            "Для гри перейдіть за посиланням:\n"
            "https://kod.greenhost.pw\n"
            "Якщо не відкривається — увімкніть VPN.\n"
            "Деталі — у «Допомога»."
        )

    await context.bot.send_message(chat_id=user_id, text=f"{admin_txt}\n\n{note}")
    await update.message.reply_text("✅ Відповідь доставлено.")
