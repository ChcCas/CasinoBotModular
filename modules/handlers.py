from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes
)

(
    STEP_MENU,
    STEP_CLIENT_CARD,
    STEP_CLIENT_PHONE_SEARCH,
    STEP_CLIENT_PHONE_CONFIRM,
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_CRYPTO_TYPE,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_REGISTER_NAME,
    STEP_REGISTER_PHONE,
    STEP_REGISTER_CODE,
) = range(12)

def setup_handlers(application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_MENU: [CallbackQueryHandler(menu_handler)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(conv)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Я Клієнт", callback_data="client")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")]
    ]
    text = "Вітаємо у Casino Club Telegram Bot! Оберіть дію:"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STEP_MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Ця функція ще в розробці.")
    return STEP_MENU
