# modules/handlers/navigation.py

from telegram.ext import CallbackQueryHandler, Application
from .start import start_command
from .deposit import deposit_conv
from .withdraw import withdraw_conv
from .profile import profile_conv
from modules.callbacks import CB
from modules.keyboards import nav_buttons

def register_navigation_handlers(app: Application):
    """
    1) Реєструємо усі ConversationHandler’и з group=0
    2) Додаємо загальний menu_router з group=1, який НЕ перехоплюватиме
       CALLBACKи, призначені profile_conv, deposit_conv, withdraw_conv
    """
    # —————————— Група 0: весь ваш ConversationHandler ——————————
    app.add_handler(profile_conv, group=0)
    app.add_handler(deposit_conv, group=0)
    app.add_handler(withdraw_conv, group=0)

    # —————————— Група 1: загальний роутер для всіх інших callback ——————————
    async def menu_router(update, context):
        query = update.callback_query
        data = query.data
        await query.answer()

        # Якщо “home” або “back” — перекидаємо на /start
        if data in (CB.HOME.value, CB.BACK.value):
            return await start_command(update, context)

        # Якщо “help” — надсилаємо підказку
        if data == CB.HELP.value:
            await query.message.reply_text(
                "ℹ️ /start — перезапустити бота",
                reply_markup=nav_buttons()
            )
            return

        # Якщо ніяка інша кнопка — для безпеки повернемо на /start
        return await start_command(update, context)

    app.add_handler(
        CallbackQueryHandler(menu_router, pattern=".*"),
        group=1
    )
