import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)
from modules.db import get_user
from modules.config import ADMIN_ID
from keyboards import nav_buttons
from states import (
    STEP_PROVIDER, STEP_DEPOSIT_AMOUNT, STEP_MENU
)

def register_deposit_handlers(app):
    app.add_handler(CallbackQueryHandler(start_deposit, pattern="^DEPOSIT_START$"), group=0)
    app.add_handler(CallbackQueryHandler(process_deposit_option,
        pattern="^(WITH_CARD|NO_CARD)$"), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount), group=2)

async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user = get_user(update.effective_user.id)
    buttons = []
    if user:
        buttons.append([InlineKeyboardButton("💳 Зі своєю карткою",   callback_data="WITH_CARD")])
    buttons.append([InlineKeyboardButton("🎮 Без карти (гість)", callback_data="NO_CARD")])
    buttons.append([InlineKeyboardButton("🏠 Головне меню",     callback_data="NAV_HOME")])
    await update.callback_query.message.reply_text(
        "Обрати тип поповнення:", InlineKeyboardMarkup(buttons)
    )
    return STEP_PROVIDER

async def process_deposit_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    context.user_data["guest"] = (data == "NO_CARD")
    await update.callback_query.message.reply_text(
        "Введіть суму поповнення:",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_AMOUNT

async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("Невірна сума.", reply_markup=nav_buttons())
        return STEP_DEPOSIT_AMOUNT

    user = get_user(update.effective_user.id)
    card = user[1] if user and not context.user_data.get("guest") else "Н/Д"
    ts   = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    msg  = (
        f"🆕 Поповнення від {update.effective_user.full_name} ({update.effective_user.id}):\n"
        f"Картка: {card}\n"
        f"Сума: {text}\n"
        f"🕒 {ts}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    await update.message.reply_text(
        "Заявка на поповнення відправлена адміну.",
        reply_markup=nav_buttons()
    )
    return STEP_MENU
