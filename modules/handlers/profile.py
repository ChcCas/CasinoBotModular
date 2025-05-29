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
from modules.db import search_user            # <-- використовуємо search_user, а не find_user
from modules.keyboards import nav_buttons, client_menu
from modules.states import (
    STEP_FIND_CARD_PHONE,
    STEP_CLIENT_AUTH,
)

async def start_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вхід із натискання '🔍 Пошук' у клієнтському меню."""
    await update.callback_query.answer()
    msg = await update.callback_query.message.reply_text(
        "🔍 Введіть ID або картку для пошуку:",
        reply_markup=nav_buttons()
    )
    context.user_data['base_msg_id'] = msg.message_id
    return STEP_FIND_CARD_PHONE

async def find_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка введеного ID/картки: редагуємо базове повідомлення."""
    query = update.message.text.strip()
    user = search_user(query)   # <-- тут викликаємо search_user()

    if user:
        text       = "✅ Авторизація успішна!"
        keyboard   = client_menu(is_admin=False)
        next_state = STEP_CLIENT_AUTH
    else:
        text       = "❌ Користувача не знайдено. Спробуйте ще раз:"
        keyboard   = nav_buttons()
        next_state = STEP_FIND_CARD_PHONE

    base_id = context.user_data.get('base_msg_id')
    if base_id:
        await context.bot.edit_message_text(
            text=text,
            chat_id=update.effective_chat.id,
            message_id=base_id,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

    # Якщо ще не авторизовані — підтягуємо message_id, щоб залишити в одному повідомленні
    if next_state == STEP_FIND_CARD_PHONE:
        context.user_data['base_msg_id'] = base_id
    else:
        context.user_data.pop('base_msg_id', None)

    return next_state

def register_profile_handlers(app: Application) -> None:
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_profile, pattern="^profile$")],
        states={
            STEP_FIND_CARD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_card)],
            STEP_CLIENT_AUTH:    [CallbackQueryHandler(lambda u, c: None)],  # тут ваші подальші хендлери
        },
        fallbacks=[],
        per_message=True
    )
    app.add_handler(conv)
