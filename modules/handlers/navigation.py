from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from modules.handlers.start import start_command

async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Просто перенаправляємо на /start
    return await start_command(update, context)

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Відправляємо головне меню без GIF
    from keyboards import main_menu
    from modules.config import ADMIN_ID
    from states import STEP_MENU

    is_admin = (update.effective_user.id == ADMIN_ID)
    await update.callback_query.message.reply_text(
        "Оберіть дію:",
        reply_markup=main_menu(is_admin=is_admin)
    )
    return STEP_MENU

def register_navigation_handlers(app):
    # Group=0, щоб ловити будь-які back/home раніше за інші колбеки
    app.add_handler(CallbackQueryHandler(go_back,  pattern="^back$"),  group=0)
    app.add_handler(CallbackQueryHandler(go_home, pattern="^home$"), group=0)