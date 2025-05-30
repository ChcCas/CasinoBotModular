from telegram.ext import Application
from .start import start_command
from .profile import profile_conv
from .deposit import deposit_conv
from .withdraw import withdraw_conv
from modules.callbacks import CB

def register_navigation_handlers(app: Application):
    # 1) окремі ConversationHandler’и
    app.add_handler(profile_conv, group=1)
    app.add_handler(deposit_conv, group=1)
    app.add_handler(withdraw_conv, group=1)

    # 2) головний роутер на інші кнопки
    from telegram.ext import CallbackQueryHandler
    async def menu_router(update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == CB.CLIENT_PROFILE.value:
            return await profile_conv.entry_points[0].callback(update, context)
        if data == CB.CLIENT_FIND.value:
            return await profile_conv.entry_points[0].callback(update, context)
        if data == CB.HELP.value:
            await update.callback_query.message.reply_text("ℹ️ Допомога…", reply_markup=nav_buttons())
            return
        # …інші кнопки…
        # default → перезапуск
        return await start_command(update, context)

    app.add_handler(CallbackQueryHandler(menu_router, pattern=".*"), group=2)
