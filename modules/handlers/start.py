import os
from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from modules.config import ADMIN_ID
from modules.keyboards import main_menu
from modules.states import STEP_MENU

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GIF_PATH = os.path.join(ROOT_DIR, "assets", "welcome.gif")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        with open(GIF_PATH, "rb") as gif:
            await update.message.reply_animation(gif)
        await update.message.reply_text(
            "Вітаємо у BIG GAME MONEY! Оберіть дію:",
            reply_markup=main_menu(is_admin=(update.effective_user.id == ADMIN_ID))
        )
    else:
        query = update.callback_query
        await query.answer()
        with open(GIF_PATH, "rb") as gif:
            await query.message.reply_animation(gif)
        await query.message.reply_text(
            "Вітаємо у BIG GAME MONEY! Оберіть дію:",
            reply_markup=main_menu(is_admin=(query.from_user.id == ADMIN_ID))
        )
    return STEP_MENU

def register_start_handler(app):
    app.add_handler(CommandHandler("start", start_command), group=0)
    app.add_handler(CallbackQueryHandler(start_command, pattern="^home$"), group=0)
