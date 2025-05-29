modules/handlers/navigation.py

import os import re import sqlite3 from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update from telegram.ext import ( ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes ) from modules.config import ADMIN_ID, DB_NAME from keyboards import PROVIDERS, PAYMENTS, nav_buttons, provider_buttons, payment_buttons, admin_panel_kb from states import ( STEP_MENU, STEP_CLIENT_CARD, STEP_PROVIDER, STEP_PAYMENT, STEP_DEPOSIT_AMOUNT, STEP_CONFIRM_FILE, STEP_CONFIRMATION, STEP_WITHDRAW_AMOUNT, STEP_WITHDRAW_METHOD, STEP_WITHDRAW_DETAILS, STEP_WITHDRAW_CONFIRM, STEP_REG_NAME, STEP_REG_PHONE, STEP_REG_CODE, STEP_ADMIN_SEARCH, STEP_ADMIN_BROADCAST, ) from .start import start_command from .admin import show_admin_panel

=== Ініціалізація таблиці threads ===

def _init_threads(): with sqlite3.connect(DB_NAME) as conn: conn.execute( """ CREATE TABLE IF NOT EXISTS threads ( user_id INTEGER PRIMARY KEY, base_msg_id INTEGER ) """ ) conn.commit()

=== Функція для реєстрації всіх навігаційних хендлерів ===

def register_navigation_handlers(app): _init_threads()

conv = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_command),
        CallbackQueryHandler(start_command, pattern="^home$", per_message=True),
        CallbackQueryHandler(start_command, pattern="^back$", per_message=True),
    ],
    states={
        STEP_MENU: [
            CallbackQueryHandler(menu_handler, pattern=".*", per_message=True)
        ],
        STEP_REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        STEP_REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
        STEP_REG_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_code)],
        STEP_CLIENT_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_card)],
        STEP_PROVIDER: [
            CallbackQueryHandler(
                process_provider,
                pattern="^(" + "|".join(map(re.escape, PROVIDERS)) + ")$",
                per_message=True,
            )
        ],
        STEP_PAYMENT: [
            CallbackQueryHandler(
                process_payment,
                pattern="^(" + "|".join(map(re.escape, PAYMENTS)) + ")$",
                per_message=True,
            )
        ],
        STEP_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount)],
        STEP_CONFIRM_FILE: [
            MessageHandler(
                filters.PHOTO | filters.Document.ALL | filters.VIDEO,
                process_file
            )
        ],
        STEP_CONFIRMATION: [
            CallbackQueryHandler(confirm_submission, pattern="^confirm$", per_message=True)
        ],
        STEP_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_amount)],
        STEP_WITHDRAW_METHOD: [
            CallbackQueryHandler(
                process_withdraw_method,
                pattern="^(" + "|".join(map(re.escape, PAYMENTS)) + ")$",
                per_message=True,
            )
        ],
        STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_details)],
        STEP_WITHDRAW_CONFIRM: [
            CallbackQueryHandler(confirm_withdrawal, pattern="^confirm_withdraw$", per_message=True)
        ],
        STEP_ADMIN_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search)],
        STEP_ADMIN_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast)],
    },
    fallbacks=[
        CallbackQueryHandler(start_command, pattern="^(home|back)$", per_message=True)
    ],
    per_message=True,
    per_chat=True,
    name="casino_conversation",
)

app.add_handler(conv, group=1)

=== Основна логіка меню ===

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): query = update.callback_query await query.answer() data = query.data

# Адмін-панель
if data == "admin_panel":
    return await show_admin_panel(query)

# Повернення додому або назад
if data in ("home", "back"):
    return await start_command(update, context)

# Поповнення
if data == "deposit":
    await query.message.reply_text(
        "💸 Введіть суму для поповнення:", reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

# Виведення коштів
if data in ("withdraw", "WITHDRAW_START"):
    await query.message.reply_text(
        "💳 Введіть суму для виведення:", reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_AMOUNT

# Реєстрація
if data == "register":
    await query.message.reply_text(
        "📝 Введіть ваше ім’я:", reply_markup=nav_buttons()
    )
    return STEP_REG_NAME

# Допомога
if data == "help":
    await query.message.reply_text(
        "ℹ️ Допомога:\n/start — перезапуск\n📲 Питання — через чат",
        reply_markup=nav_buttons()
    )
    return STEP_MENU

# Інші дії користувача
if data == "client":
    return await start_command(update, context)

# Якщо не збіглося нічого
return STEP_MENU

=== Обробники кроків реєстрації ===

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE): name = update.message.text.strip() context.user_data["reg_name"] = name await update.message.reply_text( "📞 Введіть номер телефону (0XXXXXXXXX):", reply_markup=nav_buttons() ) return STEP_REG_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE): phone = update.message.text.strip() if not re.match(r"^0\d{9}$", phone): await update.message.reply_text( "❗️ Невірний формат. Спробуйте ще раз:", reply_markup=nav_buttons() ) return STEP_REG_PHONE context.user_data["reg_phone"] = phone await update.message.reply_text( "🔑 Введіть 4-значний код підтвердження:", reply_markup=nav_buttons() ) return STEP_REG_CODE

async def register_code(update: Update, context: ContextTypes.DEFAULT_TYPE): code = update.message.text.strip() if not re.match(r"^\d{4}$", code): await update.message.reply_text( "❗️ Код має складатись з 4 цифр.", reply_markup=nav_buttons() ) return STEP_REG_CODE

user_id = update.effective_user.id
name = context.user_data.get("reg_name")
phone = context.user_data.get("reg_phone")

with sqlite3.connect(DB_NAME) as conn:
    conn.execute(
        "INSERT INTO registrations (user_id, name, phone) VALUES (?, ?, ?)",
        (user_id, name, phone)
    )
    conn.commit()

await update.message.reply_text(
    "✅ Реєстрація успішна! Оберіть дію:", reply_markup=nav_buttons()
)
return STEP_MENU

=== Обробники поповнення ===

async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE): card = update.message.text.strip().replace(" ", "") if not re.match(r"^\d{16}$", card): await update.message.reply_text( "❗️ Введіть коректний 16-значний номер картки:", reply_markup=nav_buttons() ) return STEP_CLIENT_CARD context.user_data["card"] = card

await update.message.reply_text(
    "🎰 Оберіть провайдера:", reply_markup=provider_buttons()
)
return STEP_PROVIDER

async def process_provider(update: Update, context: ContextTypes.DEFAULT_TYPE): provider = update.callback_query.data context.user_data["provider"] = provider

await update.callback_query.message.reply_text(
    "💳 Оберіть метод оплати:", reply_markup=payment_buttons()
)
return STEP_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE): context.user_data["payment"] = update.callback_query.data await update.callback_query.message.reply_text( "💰 Введіть суму поповнення:", reply_markup=nav_buttons() ) return STEP_DEPOSIT_AMOUNT

async def process_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE): try: amount = float(update.message.text.strip()) except ValueError: await update.message.reply_text( "❗️ Введіть коректну суму:", reply_markup=nav_buttons() ) return STEP_DEPOSIT_AMOUNT

context.user_data["amount"] = amount
await update.message.reply_text(
    "📎 Надішліть підтвердження (фото, документ або відео):",
    reply_markup=nav_buttons()
)
return STEP_CONFIRM_FILE

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE): file_type = "document" if update.message.document else "photo" if update.message.photo else "video" context.user_data["file_type"] = file_type

kb = [
    [InlineKeyboardButton("✅ Підтвердити", callback_data="confirm")],
    [InlineKeyboardButton("◀️ Назад", callback_data="back")],
    [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
]
await update.message.reply_text(
    "✅ Натисніть підтвердити:", reply_markup=InlineKeyboardMarkup(kb)
)
return STEP_CONFIRMATION

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE): user = update.effective_user card = context.user_data.get("card") provider = context.user_data.get("provider") payment = context.user_data.get("payment") amount = context.user_data.get("amount") ftype = context.user_data.get("file_type")

with sqlite3.connect(DB_NAME) as conn:
    conn.execute(
        "INSERT INTO deposits (user_id, username, card, provider, payment, amount, file_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user.id, user.username, card, provider, payment, amount, ftype)
    )
    conn.commit()

await update.callback_query.message.reply_text(
    "💸 Поповнення збережено! Очікуйте підтвердження.",
    reply_markup=nav_buttons()
)
return STEP_MENU

=== Обробники виведення коштів ===

async def process_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE): try: amount = float(update.message.text.strip()) except ValueError: await update.message.reply_text( "❗️ Введіть коректну суму:", reply_markup=nav_buttons() ) return STEP_WITHDRAW_AMOUNT

context.user_data["withdraw_amount"] = amount
await update.message.reply_text(
    "Оберіть метод виведення:", reply_markup=payment_buttons()
)
return STEP_WITHDRAW_METHOD

async def process_withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE): method = update.callback_query.data context.user_data["withdraw_method"] = method await update.callback_query.message.reply_text( "💳 Введіть реквізити (номер картки або гаманець):",

