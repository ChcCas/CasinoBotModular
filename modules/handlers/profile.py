# modules/handlers/profile.py

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application
)
from modules.db import find_user  # ваша функція пошуку в БД
from modules.keyboards import nav_buttons, client_menu
from modules.states import (
    STEP_FIND_CARD_PHONE,
    STEP_CLIENT_AUTH,
)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Вхід від натискання "🔍 Пошук" у головному меню
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "🔍 Введіть ID або картку для пошуку:",
        reply_markup=nav_buttons()
    )
    # Зберігаємо ID цього повідомлення, щоб потім його редагувати
    context.user_data['base_msg_id'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user = find_user(query)  # повертає None або дані користувача

    if user:
        text      = "✅ Авторизація успішна!"
        keyboard  = client_menu(is_admin=False)
        next_state = STEP_CLIENT_AUTH
    else:
        text      = "❌ Користувача не знайдено. Спробуйте ще раз:"
        keyboard  = nav_buttons()
        next_state = STEP_FIND_CARD_PHONE

    base_id = context.user_data.get('base_msg_id')
    if base_id:
        # Редагуємо існуюче повідомлення
        await context.bot.edit_message_text(
            text=text,
            chat_id=update.effective_chat.id,
            message_id=base_id,
            reply_markup=keyboard
        )
    else:
        # На випадок, якщо base_msg_id загубиться
        await update.message.reply_text(text, reply_markup=keyboard)

    # Якщо ще не авторизовані — залишаємо цей же message_id,
    # щоб користувач міг спробувати ще раз у тому самому полі.
    if next_state == STEP_FIND_CARD_PHONE:
        context.user_data['base_msg_id'] = base_id
    else:
        # Після успіху чистимо
        context.user_data.pop('base_msg_id', None)

    return next_state

def register_profile_handlers(app: Application) -> None:
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_profile, pattern="^profile$")],
        states={
            STEP_FIND_CARD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)],
            STEP_CLIENT_AUTH:    [CallbackQueryHandler(lambda u,c: None)],  # ваші подальші хендлери
        },
        fallbacks=[],
        per_message=True
    )
    app.add_handler(conv)
