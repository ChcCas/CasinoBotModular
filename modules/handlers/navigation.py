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
    Реєструє:
    1) усі ConversationHandler’и в групі 0, щоби вони мали пріоритет над роутером;
    2) загальний menu_router в групі 1, який обробляє всі інші callback_query.
    """
    # 1) ConversationHandler’и для клієнтських сценаріїв
    app.add_handler(profile_conv, group=0)
    app.add_handler(deposit_conv, group=0)
    app.add_handler(withdraw_conv, group=0)

    # 2) Загальний роутер для інших кнопок
    async def menu_router(update, context):
        query = update.callback_query
        data = query.data
        await query.answer()

        # Повернення до старту (home/back)
        if data in (CB.HOME.value, CB.BACK.value):
            return await start_command(update, context)

        # Показ help
        if data == CB.HELP.value:
            await query.message.reply_text(
                "ℹ️ /start — перезапустити бота",
                reply_markup=nav_buttons()
            )
            return

        # За замовчуванням повертаємо до /start
        return await start_command(update, context)

    # Ловимо всі callback_query, що не потрапили в ConversationHandler’и
    app.add_handler(
        CallbackQueryHandler(menu_router, pattern=".*"),
        group=1
    )
