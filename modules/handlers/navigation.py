from telegram.ext import CallbackQueryHandler, Application
from .start import start_command
from .deposit import deposit_conv
from .withdraw import withdraw_conv
from .profile import profile_conv
from modules.callbacks import CB
from modules.keyboards import nav_buttons

def register_navigation_handlers(app: Application):
    # 1. Реєструємо ConversationHandler’и
    app.add_handler(profile_conv, group=1)
    app.add_handler(deposit_conv, group=1)
    app.add_handler(withdraw_conv, group=1)

    # 2. Загальний роутер для інших кнопок
    async def menu_router(update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == CB.HOME.value or data == CB.BACK.value:
            return await start_command(update, context)

        if data == CB.HELP.value:
            await update.callback_query.message.reply_text(
                "ℹ️ /start — перезапустити бота", reply_markup=nav_buttons()
            )
            return

        # default: повернутися в меню
        return await start_command(update, context)

    app.add_handler(CallbackQueryHandler(menu_router, pattern=".*"), group=2)
