import re
import html
import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME

# === Ініціалізація схеми БД ===
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
    # Нова таблиця для summary після 48 годин
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_summary (
            user_id INTEGER PRIMARY KEY,
            name    TEXT,
            phone   TEXT,
            card    TEXT
        )
    """)
    conn.commit()

# ——— Очищення старих записів після 48 годин ——————————————————————————————————
def cleanup_old_data():
    cutoff = datetime.now() - timedelta(hours=48)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        old = cur.execute(
            "SELECT user_id, card FROM deposits WHERE timestamp < ?", (cutoff_str,)
        ).fetchall()
        for user_id, card in old:
            row = cur.execute(
                "SELECT name, phone FROM registrations WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row:
                name, phone = row
                cur.execute("""
                    INSERT OR REPLACE INTO user_summary(user_id, name, phone, card)
                    VALUES (?, ?, ?, ?)
                """, (user_id, name, phone, card))
        cur.execute("DELETE FROM deposits    WHERE timestamp < ?", (cutoff_str,))
        cur.execute("DELETE FROM withdrawals WHERE timestamp < ?", (cutoff_str,))
        conn.commit()

# Виконуємо одразу при старті
cleanup_old_data()

# ——— Стани ——————————————————————————————————
(
    STEP_MENU,
    STEP_ADMIN_PANEL,
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
) = range(25)

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS = ["Карта", "Криптопереказ"]
HELP_CATEGORIES = [
    "Реєстрація/поповнення",
    "Виведення",
    "Допомога з Trustee Plus",
    "Інше"
]

# ——— Утиліти ——————————————————————————————————
def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

# ——— Хендлери “Назад” ——————————————————————————————————
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

async def back_to_client_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Введіть номер картки для поповнення:", reply_markup=nav_buttons()
    )
    return STEP_CLIENT_CARD

async def back_to_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.callback_query.message.edit_text("Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PROVIDER

async def back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS] + [
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.callback_query.message.edit_text("Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_PAYMENT

async def back_to_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await update.callback_query.message.edit_text("Оберіть метод криптопереказу:", reply_markup=InlineKeyboardMarkup(crypto_kb))
    return STEP_CRYPTO_TYPE

async def back_to_confirm_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Після переказу надшліть підтвердження (фото/документ/відео):", reply_markup=nav_buttons()
    )
    return STEP_CONFIRM_FILE

async def back_to_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("Введіть суму виведення (мінімум 200):", reply_markup=nav_buttons())
    return STEP_WITHDRAW_AMOUNT

async def back_to_withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Введіть реквізити (16 цифр картки або крипто-адресу):", reply_markup=nav_buttons()
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
        [InlineKeyboardButton("🎲 Клієнт", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")],
        [InlineKeyboardButton("📜 Історія", callback_data="history")],
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

    if d == "admin_panel":
        kb = [
            [InlineKeyboardButton("👤 Історія реєстрацій", callback_data="admin_history_reg")],
            [InlineKeyboardButton("💰 Історія поповнень", callback_data="admin_history_dep")],
            [InlineKeyboardButton("💸 Історія виведень", callback_data="admin_history_wd")],
            [InlineKeyboardButton("⏱ Історія (48 год)", callback_data="admin_history_48h")],
            [InlineKeyboardButton("✉️ Розсилка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔍 Пошук", callback_data="admin_search")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_admin")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("📊 Адмін-панель", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_ADMIN_PANEL

    if d == "deposit":
        kb = [
            [InlineKeyboardButton("Як клієнт", callback_data="deposit_card")],
            [InlineKeyboardButton("Грати без картки", callback_data="no_card")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Як бажаєте поповнити?", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_DEPOSIT_SCENARIO

    if d == "client":
        kb = [
            [InlineKeyboardButton("Ввести картку", callback_data="enter_card")],
            [InlineKeyboardButton("Зняти кешбек", callback_data="withdraw_cashback")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ]
        await query.message.edit_text("Оберіть дію:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_CLIENT_SCENARIO

    if d == "withdraw":
        await query.message.edit_text("Введіть код заявки (00-00-00-00-00-00-00):", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE

    if d == "register":
        await query.message.edit_text("Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

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
            "2️⃣ Створіть звернення до підтримки",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return STEP_HELP_CHOICE

    if d == "history":
        return await user_history(update, context)

    if d in ("back", "home"):
        return await start(update, context)

    await query.message.edit_text("Функція в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Обробка “Історії (48 год)” для адміна ——————————————————————————————————
async def admin_history_48h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    cutoff = datetime.now() - timedelta(hours=48)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_NAME) as conn:
        deps = conn.execute(
            "SELECT id,user_id,username,card,provider,payment,timestamp "
            "FROM deposits WHERE timestamp >= ? ORDER BY timestamp DESC", (cutoff_str,)
        ).fetchall()
        wds = conn.execute(
            "SELECT id,user_id,username,amount,method,details,source_code,timestamp "
            "FROM withdrawals WHERE timestamp >= ? ORDER BY timestamp DESC", (cutoff_str,)
        ).fetchall()
    text = ""
    if deps:
        text += "💰 <b>Поповнення (останні 48 год):</b>\n"
        for r in deps:
            text += f"#{r[0]} 👤{r[2]} ID{r[1]} • картка {r[3]} • {r[4]}/{r[5]} • {r[6]}\n"
    else:
        text += "💰 Поповнень за 48 годин немає.\n"
    text += "\n"
    if wds:
        text += "💸 <b>Виведення (останні 48 год):</b>\n"
        for r in wds:
            text += f"#{r[0]} 👤{r[2]} ID{r[1]} • {r[3]} • {r[4]} • реквізити {r[5]} • {r[7]}\n"
    else:
        text += "💸 Виведень за 48 годин немає.\n"
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    return STEP_ADMIN_PANEL

# ——— Далі вставте всі ваші інші хендлери (deposit_choice_handler, client_choice_handler,
# process_card, process_provider, process_payment, process_crypto_choice,
# process_file, confirm_submission, withdraw_code, withdraw_amount, withdraw_dest,
# withdraw_confirm, withdraw_ack, register_name, register_phone, register_code,
# help_choice, help_create, help_text, help_confirm, admin_broadcast_send,
# admin_search_execute, user_history, admin_reply) без змін.

# ——— Реєстрація хендлерів ——————————————————————————————————
def setup_handlers(application: Application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_MENU:        [CallbackQueryHandler(menu_handler)],
            STEP_ADMIN_PANEL: [
                CallbackQueryHandler(admin_history_48h, pattern="^admin_history_48h$"),
                CallbackQueryHandler(admin_panel_handler)
            ],
            STEP_DEPOSIT_SCENARIO: [
                CallbackQueryHandler(deposit_choice_handler),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_CLIENT_SCENARIO: [
                CallbackQueryHandler(client_choice_handler),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_CLIENT_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_card),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_PROVIDER: [
                CallbackQueryHandler(process_provider),
                CallbackQueryHandler(back_to_client_card, pattern="^back$"),
                CallbackQueryHandler(start,             pattern="^home$")
            ],
            STEP_PAYMENT: [
                CallbackQueryHandler(process_payment),
                CallbackQueryHandler(back_to_provider, pattern="^back$"),
                CallbackQueryHandler(start,            pattern="^home$")
            ],
            STEP_CRYPTO_TYPE: [
                CallbackQueryHandler(process_crypto_choice),
                CallbackQueryHandler(back_to_payment, pattern="^back$"),
                CallbackQueryHandler(start,           pattern="^home$")
            ],
            STEP_CONFIRM_FILE: [
                MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, process_file),
                CallbackQueryHandler(back_to_confirm_file, pattern="^back$"),
                CallbackQueryHandler(start,                pattern="^home$")
            ],
            STEP_CONFIRMATION: [
                CallbackQueryHandler(confirm_submission, pattern="^confirm$"),
                CallbackQueryHandler(back_to_confirm_file, pattern="^back$"),
                CallbackQueryHandler(start,                pattern="^home$")
            ],
            STEP_WITHDRAW_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_code),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount),
                CallbackQueryHandler(back_to_withdraw_amount, pattern="^back$"),
                CallbackQueryHandler(start,                     pattern="^home$")
            ],
            STEP_WITHDRAW_DEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_dest),
                CallbackQueryHandler(back_to_withdraw_dest, pattern="^back$"),
                CallbackQueryHandler(start,                   pattern="^home$")
            ],
            STEP_WITHDRAW_CONFIRM: [
                CallbackQueryHandler(withdraw_confirm, pattern="^send_withdraw$"),
                CallbackQueryHandler(back_to_withdraw_dest, pattern="^back$"),
                CallbackQueryHandler(start,                   pattern="^home$")
            ],
            STEP_WITHDRAW_ACK: [
                CallbackQueryHandler(withdraw_ack, pattern="^ack_withdraw$"),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_REG_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_REG_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone),
                CallbackQueryHandler(back_to_reg_name, pattern="^back$"),
                CallbackQueryHandler(start,             pattern="^home$")
            ],
            STEP_REG_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_code),
                CallbackQueryHandler(back_to_reg_phone, pattern="^back$"),
                CallbackQueryHandler(start,              pattern="^home$")
            ],
            STEP_HELP_CHOICE: [
                CallbackQueryHandler(help_choice, pattern="^create_help$"),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_HELP_CREATE: [
                CallbackQueryHandler(help_create),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_HELP_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, help_text),
                CallbackQueryHandler(help_choice, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_HELP_CONFIRM: [
                CallbackQueryHandler(help_confirm, pattern="^send_help$"),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_ADMIN_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_execute),
                CallbackQueryHandler(back_to_menu, pattern="^back$"),
                CallbackQueryHandler(start,       pattern="^home$")
            ],
            STEP_USER_HISTORY: [
                CallbackQueryHandler(user_history, pattern="^history$"),
                CallbackQueryHandler(back_to_menu,  pattern="^back$"),
                CallbackQueryHandler(start,         pattern="^home$")
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv)
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1
        )
