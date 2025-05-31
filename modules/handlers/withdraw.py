# modules/handlers/withdraw.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from modules.callbacks import CB
from modules.keyboards import nav_buttons, payment_buttons, client_menu
from modules.states import (
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM
)

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "💸 Введіть суму для виведення:",
        reply_markup=nav_buttons()
    )
    context.user_data['base_msg'] = msg.message_id
    return STEP_WITHDRAW_AMOUNT

async def withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❗️ Введіть коректну суму:",
            reply_markup=nav_buttons()
        )
        return STEP_WITHDRAW_AMOUNT

    context.user_data["withdraw_amount"] = amt
    base_id = context.user_data['base_msg']

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text=f"💸 Сума для виведення: {amt}\nОберіть метод:",
        reply_markup=payment_buttons()
    )
    return STEP_WITHDRAW_METHOD

async def withdraw_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    method = update.callback_query.data
    context.user_data["withdraw_method"] = method
    base_id = context.user_data['base_msg']

    await update.callback_query.message.edit_text(
        text=f"💸 Метод: {method}\nВведіть реквізити:",
        reply_markup=nav_buttons()
    )
    return STEP_WITHDRAW_DETAILS

async def withdraw_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text.strip()
    context.user_data["withdraw_details"] = details
    base_id = context.user_data['base_msg']

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Підтвердити", callback_data=CB.WITHDRAW_CONFIRM.value)],
        [InlineKeyboardButton("🚫 Скасувати",    callback_data=CB.BACK.value)],
    ])
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=base_id,
        text=(
            f"💸 Підтвердіть виведення:\n"
            f"• Сума: {context.user_data['withdraw_amount']}\n"
            f"• Метод: {context.user_data['withdraw_method']}\n"
            f"• Реквізити: {details}"
        ),
        reply_markup=kb
    )
    return STEP_WITHDRAW_CONFIRM

async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    amt    = context.user_data["withdraw_amount"]
    method = context.user_data["withdraw_method"]
    await update.callback_query.message.edit_text(
        f"🎉 Ваш запит на виведення {amt} ({method}) успішно прийнято.\n"
        "Очікуйте підтвердження.",
        reply_markup=client_menu(is_authorized=True)
    )
    context.user_data.clear()
    return ConversationHandler.END

withdraw_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(withdraw_start, pattern=f"^{CB.WITHDRAW_START.value}$")
    ],
    states={
        STEP_WITHDRAW_AMOUNT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount)],
        STEP_WITHDRAW_METHOD:  [CallbackQueryHandler(withdraw_method, pattern="^Карта$|^Криптопереказ$")],
        STEP_WITHDRAW_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_details)],
        STEP_WITHDRAW_CONFIRM: [CallbackQueryHandler(withdraw_confirm, pattern=f"^{CB.WITHDRAW_CONFIRM.value}$")],
    },
    fallbacks=[
        CallbackQueryHandler(withdraw_start, pattern=f"^{CB.BACK.value}$")
    ],
    per_chat=True,
)

def register_withdraw_handlers(app: "Application") -> None:
    app.add_handler(withdraw_conv, group=0)
