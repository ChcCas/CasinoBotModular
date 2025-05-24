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
    conn.commit()

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

PROVIDERS       = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS        = ["Карта", "Криптопереказ"]
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
        "📥 Введіть номер картки для поповнення:", reply_markup=nav_buttons()
    )
    return STEP_CLIENT_CARD

async def back_to_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.callback_query.message.edit_text(
        "🏭 Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb)
    )
    return STEP_PROVIDER

async def back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    await update.callback_query.message.edit_text(
        "💳 Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb)
    )
    return STEP_PAYMENT

async def back_to_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    crypto_kb = [
        [InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
        [InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
        [InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back"),
         InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await update.callback_query.message.edit_text(
        "🔐 Оберіть криптопереказ:", reply_markup=InlineKeyboardMarkup(crypto_kb)
    )
    return STEP_CRYPTO_TYPE

async def back_to_confirm_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "📤 Надішліть підтвердження (фото/документ/відео):", reply_markup=nav_buttons()
    )
    return STEP_CONFIRM_FILE

async def back_to_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "💰 Введіть суму виведення (мінімум 200):", reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_AMOUNT

async def back_to_withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "📥 Введіть реквізити (16 цифр картки або крипто-адресу):", reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DEST

async def back_to_reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "📝 Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons()
    )
    return STEP_REG_PHONE

async def back_to_reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "👤 Введіть ім’я або нікнейм:", reply_markup=nav_buttons()
    )
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

# ——— Головне меню ——————————————————————————————————
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    d = query.data

    if d == "admin_panel":
        return await admin_panel_handler(update, context)

    if d == "deposit":
        kb = [
            [InlineKeyboardButton("Як клієнт", callback_data="deposit_card")],
            [InlineKeyboardButton("Грати без картки", callback_data="no_card")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
        ]
        await query.message.edit_text("💰 Як бажаєте поповнити?", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_DEPOSIT_SCENARIO

    if d == "client":
        kb = [
            [InlineKeyboardButton("Ввести картку", callback_data="enter_card")],
            [InlineKeyboardButton("Зняти кешбек", callback_data="withdraw_cashback")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
        ]
        await query.message.edit_text("🎲 Оберіть дію клієнта:", reply_markup=InlineKeyboardMarkup(kb))
        return STEP_CLIENT_SCENARIO

    if d == "withdraw":
        await query.message.edit_text("🔑 Введіть код заявки (00-00-00-00-00-00-00):", reply_markup=nav_buttons())
        return STEP_WITHDRAW_CODE

    if d == "register":
        await query.message.edit_text("📝 Введіть ім’я або нікнейм:", reply_markup=nav_buttons())
        return STEP_REG_NAME

    if d == "help":
        kb = [
            [InlineKeyboardButton("Перейти в канал", url="https://t.me/bgm_info")],
            [InlineKeyboardButton("Створити звернення", callback_data="create_help")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back"),
             InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
        ]
        await query.message.edit_text(
            "ℹ️ Якщо не знайшли відповіді:\n"
            "1️⃣ Перейдіть в канал @bgm_info\n"
            "2️⃣ Створіть звернення у боті",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return STEP_HELP_CHOICE

    if d == "history":
        return await user_history(update, context)

    if d in ("back", "home"):
        return await start(update, context)

    await query.message.edit_text("⚙️ Функція в розробці.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Адмін-панель ——————————————————————————————————
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    kb = [
        [InlineKeyboardButton("👤 Історія реєстрацій", callback_data="admin_history_reg")],
        [InlineKeyboardButton("💰 Історія поповнень", callback_data="admin_history_dep")],
        [InlineKeyboardButton("💸 Історія виведень", callback_data="admin_history_wd")],
        [InlineKeyboardButton("✉️ Розсилка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔍 Пошук", callback_data="admin_search")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_admin")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("🛠 Адмін-панель", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_PANEL

# ——— Історія реєстрацій ——————————————————————————————————
async def admin_history_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT id,user_id,name,phone,status,timestamp FROM registrations "
            "WHERE timestamp >= datetime('now','-48 hours') ORDER BY timestamp DESC"
        ).fetchall()
    if not rows:
        text = "📋 Жодної реєстрації за останні 48 годин."
    else:
        text = "\n\n".join(
            f"#{r[0]} | 👤 {r[2]} (@ID:{r[1]}) | 📞 {r[3]} | [{r[4]}] | ⏰ {r[5]}"
            for r in rows
        )
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("📋 Історія реєстрацій (48h):\n\n" + text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_PANEL

# ——— Історія поповнень ——————————————————————————————————
async def admin_history_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT id,user_id,username,card,provider,payment,timestamp FROM deposits "
            "WHERE timestamp >= datetime('now','-48 hours') ORDER BY timestamp DESC"
        ).fetchall()
    if not rows:
        text = "💰 Жодного поповнення за останні 48 годин."
    else:
        text = "\n\n".join(
            f"#{r[0]} | 👤 @{r[2]}({r[1]})\n"
            f"    🏷 Карта: {r[3]}\n"
            f"    🏭 Провайдер: {r[4]}\n"
            f"    💳 Метод: {r[5]}\n"
            f"    ⏰ {r[6]}"
            for r in rows
        )
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("💰 Історія поповнень (48h):\n\n" + text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_PANEL

# ——— Історія виведень ——————————————————————————————————
async def admin_history_wd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    with sqlite3.connect(DB_NAME) as conn:
        rows = conn.execute(
            "SELECT id,user_id,username,amount,method,details,source_code,timestamp FROM withdrawals "
            "WHERE timestamp >= datetime('now','-48 hours') ORDER BY timestamp DESC"
        ).fetchall()
    if not rows:
        text = "💸 Жодного виведення за останні 48 годин."
    else:
        text = "\n\n".join(
            f"#{r[0]} | 👤 @{r[2]}({r[1]})\n"
            f"    💰 Сума: {r[3]}\n"
            f"    🏷 Метод: {r[4]}\n"
            f"    📥 Реквізити: {r[5]}\n"
            f"    🔢 Код: {r[6]}\n"
            f"    ⏰ {r[7]}"
            for r in rows
        )
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("💸 Історія виведень (48h):\n\n" + text, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_PANEL

# ——— Розсилка всім користувачам ——————————————————————————————————
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("✉️ Введіть текст для розсилки:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    with sqlite3.connect(DB_NAME) as conn:
        users = conn.execute("SELECT DISTINCT user_id FROM registrations").fetchall()
    for (uid,) in users:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except:
            pass
    await update.message.reply_text("✅ Розсилка виконана.", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Пошук по користувачу ——————————————————————————————————
async def admin_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    kb = [
        [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
    ]
    await query.message.edit_text("🔍 Введіть user_id або username для пошуку:", reply_markup=InlineKeyboardMarkup(kb))
    return STEP_ADMIN_SEARCH

async def admin_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    param = update.message.text.strip()
    uid = int(param) if param.isdigit() else None
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        regs = deps = wds = ths = []
        hdr = f"Результати для '{param}'"
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
    sections = [f"🔎 {hdr}"]
    sections.append(
        "📋 Реєстрації:\n" +
        ("\n".join(f"#{r[0]} | {r[2]}|{r[3]}|[{r[4]}]|{r[5]}" for r in regs) or "немає")
    )
    sections.append(
        "💰 Поповнення:\n" +
        ("\n".join(f"#{r[0]} | {r[2]}|{r[3]}/{r[4]}/{r[5]}/{r[6]}" for r in deps) or "немає")
    )
    sections.append(
        "💸 Виведення:\n" +
        ("\n".join(f"#{r[0]} | {r[2]}|{r[3]}/{r[4]}/{r[5]}/код:{r[6]}/{r[7]}" for r in wds) or "немає")
    )
    sections.append(
        "💬 Ланцюги повідомлень:\n" +
        ("\n".join(f"{r[0]}↔{r[1]}(prov={r[2]})" for r in ths) or "немає")
    )
    await update.message.reply_text("\n\n".join(sections), reply_markup=nav_buttons())
    return STEP_MENU

# ——— Особиста історія клієнта ——————————————————————————————————
async def user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    with sqlite3.connect(DB_NAME) as conn:
        deps = conn.execute(
            "SELECT card,provider,payment,timestamp FROM deposits WHERE user_id=? ORDER BY timestamp DESC",
            (uid,)
        ).fetchall()
        wds = conn.execute(
            "SELECT amount,method,details,source_code,timestamp FROM withdrawals WHERE user_id=? ORDER BY timestamp DESC",
            (uid,)
        ).fetchall()
        ths = conn.execute(
            "SELECT admin_msg_id,user_msg_id,provider FROM threads WHERE user_id=? ORDER BY admin_msg_id DESC",
            (uid,)
        ).fetchall()
    deps_text = "\n".join(f"• {r[3]} — {r[1]}/{r[2]}/карта {r[0]}" for r in deps) or "немає"
    wds_text = "\n".join(f"• {r[4]} — {r[1]}/{r[2]}/{r[3]}" for r in wds) or "немає"
    ths_text = "\n".join(f"• {r[0]}↔{r[1]}({r[2]})" for r in ths) or "немає"
    text = (
        "📜 *Ваша історія*\n\n"
        f"🔹 Поповнення:\n{deps_text}\n\n"
        f"🔸 Виведення:\n{wds_text}\n\n"
        f"💬 Повідомлення:\n{ths_text}"
    )
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=nav_buttons())
    return STEP_MENU

# ——— Відповідь адміна на заявку ——————————————————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    if not orig:
        return
    admin_msg_id = orig.message_id
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(
            "SELECT user_id,provider FROM threads WHERE admin_msg_id=?",
            (admin_msg_id,)
        ).fetchone()
    if not row:
        await update.message.reply_text("❌ Не знайдено користувача для відповіді.")
        return
    user_id, provider = row
    txt = update.message.text.strip()
    note = (
        "🎰 Для гри натисніть 🎰 в лівому нижньому куті бота."
        if provider == "🏆 CHAMPION"
        else "🌐 Для гри перейдіть за https://kod.greenhost.pw (увімкніть VPN)."
    )
    await context.bot.send_message(chat_id=user_id, text=f"{txt}\n\n{note}")
    await update.message.reply_text("✅ Відповідь надіслано клієнту.")

# ——— Реєстрація хендлерів ——————————————————————————————————
def setup_handlers(application: Application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={

            STEP_MENU:        [CallbackQueryHandler(menu_handler)],
            STEP_ADMIN_PANEL: [
                CallbackQueryHandler(admin_panel_handler, pattern="^admin_panel$"),
                CallbackQueryHandler(admin_history_reg,     pattern="^admin_history_reg$"),
                CallbackQueryHandler(admin_history_dep,     pattern="^admin_history_dep$"),
                CallbackQueryHandler(admin_history_wd,      pattern="^admin_history_wd$"),
                CallbackQueryHandler(admin_broadcast,       pattern="^admin_broadcast$"),
                CallbackQueryHandler(admin_search,          pattern="^admin_search$"),
                CallbackQueryHandler(back_to_menu,          pattern="^(back_admin|home)$")
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

    # Відповіді адміністратора на заявки
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY, admin_reply),
        group=1
    )
