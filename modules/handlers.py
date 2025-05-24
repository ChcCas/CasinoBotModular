import re
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME

# === Инициализация схемы БД ===
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            admin_msg_id INTEGER PRIMARY KEY,
            user_id       INTEGER,
            user_msg_id   INTEGER,
            provider      TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS helps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

# ——— Стани ——————————————————————————————————
(
    STEP_MENU,
    STEP_DEPOSIT_SCENARIO,
    STEP_CLIENT_SCENARIO,
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
    STEP_HELP_CHOICE,
    STEP_HELP_CREATE,
    STEP_HELP_TEXT,
    STEP_HELP_CONFIRM,
    STEP_ADMIN_BROADCAST,
    STEP_ADMIN_SEARCH,
    STEP_USER_HISTORY,
) = range(24)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]
HELP_CATEGORIES = [
    "Реєстрація/поповнення",
    "Виведення",
    "Допомога з Trustee Plus",
    "Інше"
]

# ——— Кнопки «Назад» та «Головне меню» ——————————————————————————————————
def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

# ——— Хендлери повернення назад ——————————————————————————————————
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return STEP_MENU

async def back_to_client_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Введіть номер картки для поповнення:", reply_markup=nav_buttons()
    )
    return STEP_CLIENT_CARD

async def back_to_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.callback_query.message.edit_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.callback_query.message.edit_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def back_to_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.callback_query.message.edit_text("Оберіть метод криптопереказу:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE

async def back_to_confirm_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Після переказу надшліть підтвердження:", reply_markup=nav_buttons()
    )
    return STEP_CONFIRM_FILE

async def back_to_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("Введіть суму виводу (мінімум 200):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_AMOUNT

async def back_to_withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Введіть реквізити:\n– 16 цифр картки\n– або крипто-адресу",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DEST

async def back_to_reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def back_to_reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
    return STEP_REG_NAME

# ——— /start ——————————————————————————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🎲 Клієнт",       callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація",   callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",     callback_data="help")],
        [InlineKeyboardButton("📜 Історія",      callback_data="history")],
    ]
    if update.effective_user.id == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    text = "BIG BAME MONEY"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_MENU

# ——— Головне меню та адмін-панель ——————————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    d = query.data

    # Адмін-панель
    if d == "admin_panel":
        kb = [
            [InlineKeyboardButton("👤 Історія реєстрацій", callback_data="admin_history_reg")],
            [InlineKeyboardButton("💰 Історія поповнень",  callback_data="admin_history_dep")],
            [InlineKeyboardButton("💸 Історія виведень",    callback_data="admin_history_wd")],
            [InlineKeyboardButton("✉️ Розсилка",           callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔍 Пошук",               callback_data="admin_search")],
            [InlineKeyboardButton("🏠 Головне меню",        callback_data="home")],
        ]
        await query.message.edit_text("Панель адміністратора:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_MENU

    # Поповнити
    if d == "deposit":
        kb = [
            [InlineKeyboardButton("Як клієнт",        callback_data="deposit_card")],
            [InlineKeyboardButton("Грати без картки", callback_data="no_card")],
            [InlineKeyboardButton("◀️ Назад",         callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Як бажаєте поповнити?", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_DEPOSIT_SCENARIO

    # Клієнт
    if d == "client":
        kb = [
            [InlineKeyboardButton("Ввести номер картки", callback_data="enter_card")],
            [InlineKeyboardButton("Зняти кешбек",       callback_data="withdraw_cashback")],
            [InlineKeyboardButton("◀️ Назад",             callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню",     callback_data="home")],
        ]
        await query.message.edit_text("Оберіть дію:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_CLIENT_SCENARIO

    # Виведення
    if d == "withdraw":
        await query.message.edit_text("Введіть код заявки (00-00-00-00-00-00-00):", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE

    # Реєстрація
    if d == "register":
        await query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    # Допомога
    if d == "help":
        kb = [
            [InlineKeyboardButton("Перейти в канал", url="https://t.me/bgm_info")],
            [InlineKeyboardButton("Створити звернення", callback_data="create_help")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text(
            "Якщо не знайшли відповіді:\n"
            "1️⃣ Перейдіть в канал @bgm_info\n"
            "2️⃣ Або створіть звернення до підтримки",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return STEP_HELP_CHOICE

    # Історія
    if d == "history":
        return await user_history(update, context)

    # Назад/Головне
    if d in ("back", "home"):
        return await start(update, context)

    await query.message.edit_text("Функція ще в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Сценарій Допомога ——————————————————————————————————
async def help_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    kb = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in HELP_CATEGORIES]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await query.message.edit_text("Оберіть категорію звернення:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_HELP_CREATE

async def help_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    context.user_data["help_category"] = query.data
    await query.message.edit_text(f"Введіть текст звернення для «{query.data}»:", reply_markup=nav_buttons())
    return STEP_HELP_TEXT

async def help_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["help_text"] = update.message.text.strip()
    kb = [
        [InlineKeyboardButton("✅ Підтвердити", callback_data="send_help")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Перевірте звернення і підтвердіть:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_HELP_CONFIRM

async def help_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user
    cat  = context.user_data["help_category"]
    txt  = context.user_data["help_text"]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO helps(user_id,category,text) VALUES (?,?,?)", (user.id, cat, txt))
        conn.commit()
    # Надсилаємо звернення в канал адмінів
    await context.bot.send_message(
        chat_id="@bgmua",
        text=f"🆘 Звернення від @{user.username or user.id}\nКатегорія: {cat}\n\n{txt}"
    )
    await query.message.edit_text("✅ Заявку надіслано. Чекайте відповіді.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Сценарій “Поповнити” ——————————————————————————————————
async def deposit_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data == "deposit_card":
        await query.message.edit_text("Введіть номер картки для поповнення:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    # “Грати без картки”
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

# ——— Сценарій “Я клієнт” ——————————————————————————————————
async def client_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data == "enter_card":
        await query.message.edit_text("Введіть номер картки клубу:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    await query.message.edit_text("Функція зняття кешбеку в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Флоу поповнення ——————————————————————————————————
async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = update.message.text.strip()
    if not re.fullmatch(r"\d{4,5}", card):
        await update.message.reply_text("Невірний формат картки.", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD
    context.user_data["card"] = card
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.message.reply_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    context.user_data["provider"] = query.data
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.reply_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    choice = query.data
    context.user_data["payment"] = choice
    if choice == "Карта":
        text = (
            "Переказуйте на картку:\n"
            "Тарасюк Віталій\nОщадбанк 4790 7299 5675 1465\n"
            "Після переказу надішліть підтвердження (фото/пдф/відео)."
        )
        await query.message.reply_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.reply_text("Оберіть криптопереказ:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE

async def process_crypto_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data in ("back", "home"):
        return await menu_handler(update, context)
    choice = query.data
    context.user_data["payment"] = choice
    if choice == "Trustee Plus":
        text = "Переказуйте USDT на Trustee Plus ID: bgm001\nНадішліть підтвердження."
        await query.message.reply_text(text, reply_markup=nav_buttons())
        return STEP_CONFIRM_FILE
    await query.message.reply_text(f"Метод «{choice}» в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["file"] = update.message
    kb = [
        [InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.message.reply_text("Натисніть для підтвердження:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user     = update.effective_user
    card     = context.user_data.get("card")
    provider = context.user_data.get("provider")
    payment  = context.user_data.get("payment")
    file_msg: Message = context.user_data.get("file")

    lines = ["Нова заявка:"]
    if card:
        lines.append(f"• Картка: {card}")
    lines.append(f"• Провайдер: {provider}")
    lines.append(f"• Метод: {payment}")
    caption = "\n".join(lines)

    admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption)
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id,user_id,user_msg_id,provider) VALUES (?,?,?,?)",
            (admin_msg.message_id, user.id, file_msg.message_id, provider)
        )
        conn.execute(
            "INSERT INTO deposits(user_id,username,card,provider,payment,file_type) VALUES (?,?,?,?,?,?)",
            (user.id, user.username or "", card or "", provider, payment,
             file_msg.effective_attachment.__class__.__name__)
        )
        conn.commit()

    await query.message.edit_text("✅ Заявка надіслана.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Флоу виведення ——————————————————————————————————
async def withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not re.fullmatch(r'(?:\d{2}-){6}\d{2}', code):
        await update.message.reply_text("Невірний код.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE
    context.user_data["withdraw_code"] = code
    await update.message.reply_text("Введіть суму (мінімум 200):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = update.message.text.strip()
    if not amt.isdigit() or int(amt) < 200:
        await update.message.reply_text("Некоректна сума.", reply_markup=nav_buttons())
        return STEP_WITHDRAW_AMOUNT
    context.user_data["withdraw_amount"] = amt
    await update.message.reply_text("Введіть реквізити (16 цифр карти або крипто-адресу):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_DEST

async def withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest = update.message.text.strip()
    method = 'card' if re.fullmatch(r'\d{16}', dest) else 'crypto'
    context.user_data["withdraw_method"] = method
    context.user_data["withdraw_dest"]   = dest
    kb = [[InlineKeyboardButton("✅ Надіслати заявку", callback_data="send_withdraw")],
          [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]]
    await update.message.reply_text("Перевірте дані й натисніть «Надіслати заявку»", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_CONFIRM

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user   = update.effective_user
    code   = context.user_data["withdraw_code"]
    amount = context.user_data["withdraw_amount"]
    dest   = context.user_data["withdraw_dest"]

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO withdrawals(user_id,username,amount,method,details,source_code) VALUES (?,?,?,?,?,?)",
            (user.id, user.username or "", amount, context.user_data["withdraw_method"], dest, code)
        )
        conn.commit()

    await context.bot.send_message(chat_id=ADMIN_ID,
        text=f"🛎 Заявка на виведення:\nКод: {code}\nСума: {amount}\nРеквізити: {dest}"
    )
    kb = [[InlineKeyboardButton("Підтверджую отримання", callback_data="ack_withdraw")]]
    await query.message.edit_text("✅ Заявку відправлено. Після отримання натисніть:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_WITHDRAW_ACK

async def withdraw_ack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = update.effective_user
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"✔️ @{user.username or user.id} підтвердив отримання.")
    await query.message.edit_text("✅ Дякуємо!", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Флоу реєстрації ——————————————————————————————————
async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons())
    return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not re.fullmatch(r"0\d{9}", phone):
        await update.message.reply_text("Невірний телефон.", reply_markup=nav_buttons())
        return STEP_REG_PHONE
    context.user_data["reg_phone"] = phone
    name = context.user_data["reg_name"]
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Нова реєстрація: {name} | {phone}")
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            "INSERT INTO registrations(user_id,name,phone) VALUES (?,?,?)",
            (update.effective_user.id, name, phone)
        )
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
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Код підтвердження від {name} ({user.id}): {code}")
    kb = [[InlineKeyboardButton("💰 Поповнити", callback_data="deposit")], [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]]
    await update.message.reply_text("Реєстрацію надіслано!", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_MENU

# ——— Адмін: розсилка та пошук ——————————————————————————————————
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

async def admin_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    param = update.message.text.strip()
    uid = int(param) if param.isdigit() else None
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        regs = deps = wds = ths = []
        hdr = f"Результати для '{param}'"
        if uid:
            regs = cur.execute("SELECT id,user_id,name,phone,status,timestamp FROM registrations WHERE user_id=?", (uid,)).fetchall()
            deps = cur.execute("SELECT id,user_id,username,card,provider,payment,timestamp FROM deposits WHERE user_id=?", (uid,)).fetchall()
            wds = cur.execute("SELECT id,user_id,username,amount,method,details,source_code,timestamp FROM withdrawals WHERE user_id=?", (uid,)).fetchall()
            ths = cur.execute("SELECT admin_msg_id,user_msg_id,provider FROM threads WHERE user_id=?", (uid,)).fetchall()
            hdr = f"Результати для user_id={uid}"
    sections = [f"🔎 {hdr}"]
    sections.append("Реєстрації:\n" + ("\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|[{r[4]}]|{r[5]}" for r in regs) or "немає"))
    sections.append("Поповнення:\n" + ("\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}" for r in deps) or "немає"))
    sections.append("Виведення:\n" + ("\n".join(f"#{r[0]} uid:{r[1]} {r[2]}|{r[3]}|{r[4]}|{r[5]}|код:{r[6]}|{r[7]}" for r in wds) or "немає"))
    sections.append("Повідомлення:\n" + ("\n".join(f"admin_msg_id={r[0]} ↔ user_msg_id={r[1]} (prov={r[2]})" for r in ths) or "немає"))
    await update.message.reply_text("\n\n".join(sections), reply_markup=nav_buttons())
    return STEP_MENU

# ——— Особиста історія клієнта ——————————————————————————————————
async def user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    with sqlite3.connect(DB_NAME) as conn:
        deps = conn.execute("SELECT card,provider,payment,timestamp FROM deposits WHERE user_id=? ORDER BY timestamp DESC", (uid,)).fetchall()
        wds = conn.execute("SELECT amount,method,details,source_code,timestamp FROM withdrawals WHERE user_id=? ORDER BY timestamp DESC", (uid,)).fetchall()
        ths = conn.execute("SELECT admin_msg_id,user_msg_id,provider FROM threads WHERE user_id=? ORDER BY admin_msg_id DESC", (uid,)).fetchall()
    deps_text = "\n".join(f"• {r[3]} — {r[1]}/{r[2]}/карта {r[0]}" for r in deps) or "немає"
    wds_text = "\n".join(f"• {r[4]} — {r[1]}/{r[2]}/{r[3]}" for r in wds) or "немає"
    ths_text = "\n".join(f"• {r[0]}↔{r[1]}({r[2]})" for r in ths) or "немає"
    text = f"📜 Ваша історія\n\n🔹Поповнення:\n{deps_text}\n\n🔸Виведення:\n{wds_text}\n\n💬Повідомлення:\n{ths_text}"
    await query.message.edit_text(text, reply_markup=nav_buttons())
    return STEP_MENU

# ——— Відповідь адміна на заявку ——————————————————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    admin_msg_id = orig.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id,provider FROM threads WHERE admin_msg_id=?", (admin_msg_id,)).fetchone()
    if not row:
        await update.message.reply_text("❌ Не знайдено користувача.")
        return
    user_id, provider = row
    txt = update.message.text.strip()
    if provider == "🏆 CHAMPION":
        note = "Дякуємо за CHAMPION! Для гри натисніть 🎰 в лівому нижньому куті бота."
    else:
        note = "Для гри: https://kod.greenhost.pw (увімкніть VPN при потребі)."
    await context.bot.send_message(chat_id=user_id, text=f"{txt}\n\n{note}")
    await update.message.reply_text("✅ Відповідь доставлено.")

# ——— Реєстрація хендлерів ——————————————————————————————————
def setup_handlers(application: Application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={

            STEP_MENU: [CallbackQueryHandler(menu_handler)],

            STEP_DEPOSIT_SCENARIO: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(deposit_choice_handler),
            ],
            STEP_CLIENT_SCENARIO: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(client_choice_handler),
            ],

            STEP_CLIENT_CARD: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card),
            ],
            STEP_PROVIDER: [
                CallbackQueryHandler(back_to_client_card, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(process_provider),
            ],
            STEP_PAYMENT: [
                CallbackQueryHandler(back_to_provider, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(process_payment),
            ],
            STEP_CRYPTO_TYPE: [
                CallbackQueryHandler(back_to_payment, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(process_crypto_choice),
            ],
            STEP_CONFIRM_FILE: [
                CallbackQueryHandler(back_to_payment, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file),
            ],
            STEP_CONFIRMATION: [
                CallbackQueryHandler(back_to_confirm_file, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(confirm_submission, pattern="^confirm$"),
            ],

            STEP_WITHDRAW_CODE: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_code),
            ],
            STEP_WITHDRAW_AMOUNT: [
                CallbackQueryHandler(back_to_withdraw_amount, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount),
            ],
            STEP_WITHDRAW_DEST: [
                CallbackQueryHandler(back_to_withdraw_dest, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_dest),
            ],
            STEP_WITHDRAW_CONFIRM: [
                CallbackQueryHandler(back_to_withdraw_dest, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(withdraw_confirm, pattern="^send_withdraw$"),
            ],
            STEP_WITHDRAW_ACK: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(withdraw_ack, pattern="^ack_withdraw$"),
            ],

            STEP_REG_NAME: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
            ],
            STEP_REG_PHONE: [
                CallbackQueryHandler(back_to_reg_name, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
            ],
            STEP_REG_CODE: [
                CallbackQueryHandler(back_to_reg_phone, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),
            ],

            STEP_HELP_CHOICE: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(help_choice, pattern="^create_help$"),
            ],
            STEP_HELP_CREATE: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(help_create),
            ],
            STEP_HELP_TEXT: [
                CallbackQueryHandler(back_to_help_create := help_choice, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, help_text),
            ],
            STEP_HELP_CONFIRM: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(help_confirm, pattern="^send_help$"),
            ],

            STEP_ADMIN_BROADCAST: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
            ],
            STEP_ADMIN_SEARCH: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_execute),
            ],

            STEP_USER_HISTORY: [
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^home$"),
                CallbackQueryHandler(user_history, pattern="^history$")
            ],

        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1
                                 )
