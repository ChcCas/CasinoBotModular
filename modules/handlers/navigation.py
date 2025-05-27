# modules/handlers/navigation.py

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from modules.handlers.start import start_command

async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник кнопки '🏠 Головне меню' — просто перенаправляє на /start."""
    # Якщо це callback_query — відповідаємо, а потім викликаємо start_command
    await update.callback_query.answer()
    # Викликаємо той самий start_command, що й при /start
    return await start_command(update, context)

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник кнопки '◀️ Назад' — повертає до STEP_MENU."""
    await update.callback_query.answer()
    # Просто повертаємо головне меню без GIF
    from keyboards import main_menu
    from modules.config import ADMIN_ID
    from states import STEP_MENU

    is_admin = (update.effective_user.id == ADMIN_ID)
    # Відправляємо текст «Оберіть дію» + клавіатуру
    await update.callback_query.message.reply_text(
        "Оберіть дію:",
        reply_markup=main_menu(is_admin=is_admin)
    )
    return STEP_MENU

def register_navigation_handlers(app):
    """Реєструємо кнопки 'back' та 'home' по всьому флоу."""
    app.add_handler(CallbackQueryHandler(go_back,  pattern="^back$"),  group=0)
    app.add_handler(CallbackQueryHandler(go_home, pattern="^home$"), group=0)
