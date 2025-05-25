import re
import html
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
MessageHandler, filters, ContextTypes
)
from modules.config import ADMIN_ID, DB_NAME

=== Ініціалізація схеми БД ===

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

——— Стани ——————————————————————————————————

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

——— Утиліти ——————————————————————————————————

def build_nav(show_back: bool = True, show_home: bool = True) -> InlineKeyboardMarkup:
"""
Клавіатура з кнопками ◀️ Назад і/або 🏠 Головне меню.
"""
row = []
if show_back:
row.append(InlineKeyboardButton("◀️ Назад", callback_data="back"))
if show_home:
row.append(InlineKeyboardButton("🏠 Головне меню", callback_data="home"))
return InlineKeyboardMarkup([row])

def now_kyiv() -> str:
"""Поточний час у Києві."""
return datetime.now(ZoneInfo("Europe/Kiev")).strftime("%Y-%m-%d %H:%M:%S")

——— /start ——————————————————————————————————

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

——— Меню ——————————————————————————————————

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
d = query.data

if d == "admin_panel":  
    # Адмін-панель  
    kb = [  
        [InlineKeyboardButton("👤 Історія реєстрацій", callback_data="admin_history_reg")],  
        [InlineKeyboardButton("💰 Історія поповнень", callback_data="admin_history_dep")],  
        [InlineKeyboardButton("💸 Історія виведень", callback_data="admin_history_wd")],  
        [InlineKeyboardButton("✉️ Розсилка", callback_data="admin_broadcast")],  
        [InlineKeyboardButton("🔍 Пошук", callback_data="admin_search")],  
        [InlineKeyboardButton("◀️ Назад", callback_data="back_admin")],  
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],  
    ]  
    await query.message.edit_text("📊 Адмін-панель", reply_markup=InlineKeyboardMarkup(kb))  
    return STEP_ADMIN_PANEL  

if d == "deposit":  
    # Вибір сценарію поповнення  
    kb = [  
        [InlineKeyboardButton("Як клієнт", callback_data="deposit_card")],  
        [InlineKeyboardButton("Грати без картки", callback_data="no_card")],  
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],  
    ]  
    await query.message.edit_text("Як бажаєте поповнити?", reply_markup=InlineKeyboardMarkup(kb))  
    return STEP_DEPOSIT_SCENARIO  

if d == "client":  
    # Сценарії клієнта  
    kb = [  
        [InlineKeyboardButton("Ввести картку", callback_data="enter_card")],  
        [InlineKeyboardButton("Зняти кешбек", callback_data="withdraw_cashback")],  
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],  
    ]  
    await query.message.edit_text("Оберіть дію:", reply_markup=InlineKeyboardMarkup(kb))  
    return STEP_CLIENT_SCENARIO  

if d == "withdraw":  
    await query.message.edit_text(  
        "Введіть код заявки (00-00-00-00-00-00-00):",  
        reply_markup=build_nav()  
    )  
    return STEP_WITHDRAW_CODE  

if d == "register":  
    await query.message.edit_text(  
        "Введіть ім’я або нікнейм:",  
        reply_markup=build_nav()  
    )  
    return STEP_REG_NAME  

if d == "help":  
    kb = [  
        [InlineKeyboardButton("Перейти в канал", url="https://t.me/bgm_info")],  
        [InlineKeyboardButton("Створити звернення", callback_data="create_help")],  
        [InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")],  
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

# Фallback  
await query.message.edit_text("Функція в розробці.", reply_markup=build_nav())  
return STEP_MENU

——— Адмін-панель ——————————————————————————————————

async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
cmd = query.data

# Назад всередині адмін-панелі  
if cmd == "back_admin":  
    return await menu_handler(update, context)  
if cmd == "home":  
    return await start(update, context)  

# Історія реєстрацій  
if cmd == "admin_history_reg":  
    with sqlite3.connect(DB_NAME) as conn:  
        rows = conn.execute(  
            "SELECT id,user_id,name,phone,status,timestamp FROM registrations ORDER BY timestamp DESC"  
        ).fetchall()  
    text = "Немає реєстрацій." if not rows else "\n\n".join(  
        f"#{r[0]} 👤 {r[2]} (@ID:{r[1]}) | 📞{r[3]} | [{r[4]}] | ⏰{r[5]}"  
        for r in rows  
    )  
    await query.message.edit_text(  
        f"📋 Історія реєстрацій:\n\n{text}",  
        reply_markup=build_nav(show_back=True)  
    )  
    return STEP_ADMIN_PANEL  

# Історія поповнень  
if cmd == "admin_history_dep":  
    with sqlite3.connect(DB_NAME) as conn:  
        rows = conn.execute(  
            "SELECT id,user_id,username,card,provider,payment,timestamp FROM deposits ORDER BY timestamp DESC"  
        ).fetchall()  
    text = "Немає поповнень." if not rows else "\n\n".join(  
        f"#{r[0]} 👤 {r[2]} (@ID:{r[1]})\n"  
        f"   🏷 Картка: {r[3]}\n   🏭 Провайдер: {r[4]}\n   💳 Метод: {r[5]}\n   ⏰ {r[6]}"  
        for r in rows  
    )  
    await query.message.edit_text(  
        f"💰 Історія поповнень:\n\n{text}",  
        reply_markup=build_nav(show_back=True)  
    )  
    return STEP_ADMIN_PANEL  

# Історія виведень  
if cmd == "admin_history_wd":  
    with sqlite3.connect(DB_NAME) as conn:  
        rows = conn.execute(  
            "SELECT id,user_id,username,amount,method,details,source_code,timestamp FROM withdrawals ORDER BY timestamp DESC"  
        ).fetchall()  
    text = "Немає виведень." if not rows else "\n\n".join(  
        f"#{r[0]} 👤 {r[2]} (@ID:{r[1]})\n"  
        f"   💸 Сума: {r[3]}\n   🏷 Метод: {r[4]}\n   📥 Реквізити: {r[5]}\n   🔢 Код: {r[6]}\n   ⏰ {r[7]}"  
        for r in rows  
    )  
    await query.message.edit_text(  
        f"📄 Історія виведень:\n\n{text}",  
        reply_markup=build_nav(show_back=True)  
    )  
    return STEP_ADMIN_PANEL  

# Розсилка  
if cmd == "admin_broadcast":  
    await query.message.edit_text(  
        "✉️ Введіть текст для розсилки:",  
        reply_markup=build_nav()  
    )  
    return STEP_ADMIN_BROADCAST  

# Пошук  
if cmd == "admin_search":  
    await query.message.edit_text(  
        "🔍 Введіть user_id або username для пошуку:",  
        reply_markup=build_nav()  
    )  
    return STEP_ADMIN_SEARCH  

return STEP_ADMIN_PANEL

——— “Допомога” ——————————————————————————————————

async def help_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
kb = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in HELP_CATEGORIES]
kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
await query.message.edit_text("🆘 Оберіть категорію звернення:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_HELP_CREATE

async def help_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
context.user_data["help_category"] = query.data
await query.message.edit_text(f"✍️ Введіть текст зверення для «{query.data}»:", reply_markup=build_nav())
return STEP_HELP_TEXT

async def help_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["help_text"] = update.message.text.strip()
kb = [
[InlineKeyboardButton("✅ Підтвердити", callback_data="send_help")],
[InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
]
await update.message.reply_text("🔎 Перевірте звернення і підтвердіть:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_HELP_CONFIRM

async def help_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
user = update.effective_user
cat = context.user_data["help_category"]
txt = context.user_data["help_text"]
ts  = now_kyiv()
with sqlite3.connect(DB_NAME) as conn:
conn.execute("INSERT INTO helps(user_id,category,text) VALUES (?,?,?)", (user.id, cat, txt))
conn.commit()
await context.bot.send_message(
chat_id="@bgmua",
text=(
f"🆘 Нове звернення\n"
f"👤 {html.escape(user.full_name)} (@{html.escape(user.username or str(user.id))})\n"
f"📂 Категорія: {html.escape(cat)}\n"
f"⏰ {ts}\n\n"
f"{html.escape(txt)}"
),
parse_mode="Markdown"
)
await query.message.edit_text("✅ Заявку надіслано. Чекайте відповіді.", reply_markup=build_nav())
return STEP_MENU

——— “Поповнити” ——————————————————————————————————

async def deposit_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
if query.data == "deposit_card":
await query.message.edit_text("📥 Введіть номер картки для поповнення:", reply_markup=build_nav())
return STEP_CLIENT_CARD
kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
await query.message.edit_text("🏭 Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_PROVIDER

async def client_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
if query.data == "enter_card":
await query.message.edit_text("📥 Введіть номер картки клубу:", reply_markup=build_nav())
return STEP_CLIENT_CARD
await query.message.edit_text("🎁 Функція зняття кешбеку в розробці.", reply_markup=build_nav())
return STEP_MENU

——— Флоу поповнення ——————————————————————————————————

async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
card = update.message.text.strip()
if not re.fullmatch(r"\d{4,5}", card):
await update.message.reply_text("❗ Невірний формат картки.", reply_markup=build_nav())
return STEP_CLIENT_CARD
context.user_data["card"] = card
kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
await update.message.reply_text("🏭 Оберіть провайдера:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
if query.data in ("back", "home"):
return await start(update, context)
context.user_data["provider"] = query.data
kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
await query.message.reply_text("💳 Оберіть метод оплати:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
if query.data in ("back", "home"):
return await start(update, context)
choice = query.data
context.user_data["payment"] = choice
if choice == "Карта":
await query.message.reply_text(
"💵 Переказуйте на картку:\n"
"Тарасюк Віталій\nОщадбанк 4790 7299 5675 1465\n\n"
"Після переказу надішліть підтвердження (фото/пдф/відео).",
reply_markup=build_nav()
)
return STEP_CONFIRM_FILE
# крипто-сценарій
crypto_kb = [
[InlineKeyboardButton("Trustee Plus", callback_data="Trustee Plus")],
[InlineKeyboardButton("Telegram Wallet", callback_data="Telegram Wallet")],
[InlineKeyboardButton("Coinbase Wallet", callback_data="Coinbase Wallet")],
[InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
]
await query.message.reply_text("🔐 Оберіть криптопереказ:", reply_markup=InlineKeyboardMarkup(crypto_kb))
return STEP_CRYPTO_TYPE

async def process_crypto_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
if query.data in ("back", "home"):
return await start(update, context)
choice = query.data
context.user_data["payment"] = choice
if choice == "Trustee Plus":
await query.message.reply_text(
"🔗 Переказуйте USDT на Trustee Plus\nID: bgm001\n\n"
"Надішліть підтвердження (фото/документ/відео).",
reply_markup=build_nav()
)
return STEP_CONFIRM_FILE
await query.message.reply_text(f"❗ Метод «{choice}» в розробці.", reply_markup=build_nav())
return STEP_MENU

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["file"] = update.message
kb = [
[InlineKeyboardButton("✅ Надіслати", callback_data="confirm")],
[InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
]
await update.message.reply_text("📤 Натисніть для підтвердження:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query; await query.answer()
user     = update.effective_user
card     = context.user_data.get("card", "—")
provider = context.user_data.get("provider", "—")
payment  = context.user_data.get("payment", "—")
file_msg: Message = context.user_data.get("file")
ts       = now_kyiv()

safe_name     = html.escape(user.full_name)  
safe_username = html.escape(user.username or str(user.id))  
safe_card     = html.escape(card)  
safe_provider = html.escape(provider)  
safe_payment  = html.escape(payment)  

caption = (  
    f"🆕 <b>Нова заявка на поповнення</b>\n\n"  
    f"👤 Користувач: {safe_name} (@{safe_username}) [ID {user.id}]\n"  
    f"🏷 Картка: <code>{safe_card}</code>\n"  
    f"🏭 Провайдер: {safe_provider}\n"  
    f"💳 Метод: {safe_payment}\n"  
    f"📂 Тип файлу: {file_msg.effective_attachment.__class__.__name__}\n"  
    f"⏰ {ts}"  
)  

admin_msg = await file_msg.copy(chat_id=ADMIN_ID, caption=caption, parse_mode="HTML")  
with sqlite3.connect(DB_NAME) as conn:  
    conn.execute(  
        "INSERT OR REPLACE INTO threads(admin_msg_id,user_id,user_msg_id,provider) VALUES (?,?,?,?)",  
        (admin_msg.message_id, user.id, file_msg.message_id, provider)  
    )  
    conn.execute(  
        "INSERT INTO deposits(user_id,username,card,provider,payment,file_type) VALUES (?,?,?,?,?,?)",  
        (user.id, user.username or "", card, provider, payment,  
         file_msg.effective_attachment.__class__.__name__)  
    )  
    conn.commit()  

await query.message.edit_text("✅ Ваша заявка на поповнення надіслана.", reply_markup=build_nav())  
return STEP_MENU

——— “Виведення” ——————————————————————————————————

async def withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
code = update.message.text.strip()
if not re.fullmatch(r'(?:\d{2}-){6}\d{2}', code):
await update.message.reply_text("❗ Невірний формат коду.", reply_markup=build_nav())
return STEP_WITHDRAW_CODE
context.user_data["withdraw_code"] = code
await update.message.reply_text("💰 Введіть суму виведення (мінімум 200):", reply_markup=build_nav())
return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
amt = update.message.text.strip()
if not amt.isdigit() or int(amt) < 200:
await update.message.reply_text("❗ Некоректна сума.", reply_markup=build_nav())
return STEP_WITHDRAW_AMOUNT
context.user_data["withdraw_amount"] = amt
await update.message.reply_text(
"📥 Введіть реквізити для виведення:\n– 16 цифр картки або крипто-адресу",
reply_markup=build_nav()
)
return STEP_WITHDRAW_DEST

async def withdraw_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
dest = update.message.text.strip()
method = 'card' if re.fullmatch(r'\d{16}', dest) else 'crypto'
context.user_data["withdraw_method"] = method
context.user_data["withdraw_dest"] = dest
kb = [
[InlineKeyboardButton("✅ Надіслати заявку", callback_data="send_withdraw")],
[InlineKeyboardButton("◀️ Назад", callback_data="back"), InlineKeyboardButton("🏠 Головне меню", callback_data="home")]
]
await update.message.reply_text("🔍 Перевірте дані й натисніть:", reply_markup=InlineKeyboardMarkup(kb))
return STEP_WITHDRAW_CONFIRM

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
query  = update.callback_query; await query.answer()
user   = update.effective_user
code   = context.user_data["withdraw_code"]
amount = context.user_data["withdraw_amount"]
dest   = context.user_data["withdraw_dest"]
method = context.user_data["withdraw_method"]
ts     = now_kyiv()

text = (  
    f"🆕 <b>Нова заявка на виведення</b>\n\n"  
    f"👤 {html.escape(user.full_name)} (@{html.escape(user.username or str(user.id))})\n"  
    f"🔢 Код: <code>{html.escape(code)}</code>\n"  
    f"💰 Сума: {html.escape(amount)}\n"  
    f"🏷 Метод: {html.escape(method)}\n"  
    f"📥 Реквізити: <code>{html.escape(dest)}</code>\n"  
    f"⏰ {ts}"  
)  
await context.bot.se