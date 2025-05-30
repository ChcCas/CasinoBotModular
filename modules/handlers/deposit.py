from telegram import Update
from telegram.ext import (
    MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from .emails import notify_admin  # уявна функція
from modules.keyboards import nav_buttons
from modules.callbacks import CB
from modules.states import (
    STEP_DEPOSIT_AMOUNT, STEP_DEPOSIT_FILE, STEP_DEPOSIT_CONFIRM
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
    amount = update.message.text.strip()
    # можна валідувати тут…
    context.user_data['deposit_amount'] = amount
    base_id = context.user_data['base_msg']

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text=f"💰 Сума: {amount}\nЗавантажте підтверджувальний файл:",
        reply_markup=nav_buttons()
    )
    return STEP_DEPOSIT_FILE

async def deposit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document or update.message.photo[-1]
    file_id = file.file_id
    context.user_data['deposit_file_id'] = file_id
    base_id = context.user_data['base_msg']

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text="✅ Файл отримано. Підтвердити поповнення?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Підтвердити", callback_data=CB.DEPOSIT_CONFIRM.value)],
            [InlineKeyboardButton("🚫 Скасувати",   callback_data=CB.BACK.value)],
        ])
    )
    return STEP_DEPOSIT_CONFIRM

async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    amt = context.user_data['deposit_amount']
    file_id = context.user_data['deposit_file_id']
    # шлемо адміну email/SMS/будьщо
    await notify_admin(user_id=update.effective_user.id, amount=amt, file_id=file_id)

    # завершуємо
    await update.callback_query.message.edit_text(
        f"🎉 Депозит на суму {amt} підтверджено. Дякуємо!",
        reply_markup=client_menu(is_authorized=True)
    )
    context.user_data.clear()
    return ConversationHandler.END

deposit_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(deposit_start, pattern=f"^{CB.DEPOSIT_START.value}$")],
    states={
        STEP_DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)],
        STEP_DEPOSIT_FILE:   [MessageHandler(filters.Document.ALL | filters.PHOTO, deposit_file)],
        STEP_DEPOSIT_CONFIRM:[CallbackQueryHandler(deposit_confirm, pattern=f"^{CB.DEPOSIT_CONFIRM.value}$")],
    },
    fallbacks=[CallbackQueryHandler(deposit_start, pattern=f"^{CB.BACK.value}$")],
    per_message=True,
)
