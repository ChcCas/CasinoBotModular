# modules/handlers/deposit.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from modules.callbacks import CB
from modules.keyboards import nav_buttons, client_menu
from modules.states import (
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM
)

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "💰 Введіть суму депозиту:",
        reply_markup=nav_buttons()
    )
    context.user_data['base_msg'] = msg.message_id
    return STEP_DEPOSIT_AMOUNT

async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть коректну суму:",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_AMOUNT

    context.user_data['deposit_amount'] = amount
    base_id = context.user_data['base_msg']
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text=f"💰 Сума: {amount}\nЗавантажте підтвердження (фото/документ/відео):",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_FILE

async def deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    elif update.message.video:
        file_id = update.message.video.file_id
    else:
        await update.message.reply_text(
            "❗️ Надішліть фото, документ або відео як підтвердження:",
            reply_markup=nav_buttons()
        )
        return STEP_DEPOSIT_FILE

    context.user_data['deposit_file_id'] = file_id
    base_id = context.user_data['base_msg']

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)],
        [InlineKeyboardButton("🚫 Скасувати",   callback_data=CB.BACK.value)],
    ])
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text="✅ Файл отримано. Підтвердіть поповнення:",
        reply_markup=kb
    )
    return STEP_DEPOSIT_CONFIRM

async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    amount = context.user_data['deposit_amount']
    await update.callback_query.message.edit_text(
        f"🎉 Депозит на суму {amount} отримано. Очікуйте підтвердження.",
        reply_markup=client_menu(is_authorized=True)
    )
    context.user_data.clear()
    return ConversationHandler.END

deposit_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(deposit_start, pattern=f"^{CB.DEPOSIT_START.value}$")
    ],
    states={
        STEP_DEPOSIT_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)],
        STEP_DEPOSIT_FILE:    [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.VIDEO, deposit_file)],
        STEP_DEPOSIT_CONFIRM: [CallbackQueryHandler(deposit_confirm, pattern=f"^{CB.DEPOSIT_CONFIRM.value}$")],
    },
    fallbacks=[
        CallbackQueryHandler(deposit_start, pattern=f"^{CB.BACK.value}$")
    ],
    per_chat=True,
)

def register_deposit_handlers(app: "Application") -> None:
    app.add_handler(deposit_conv, group=0)
