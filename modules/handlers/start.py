 # modules/handlers/start.py

 import os
 from telegram import Update
 from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
 from modules.config import ADMIN_ID
 from keyboards import main_menu
 from states    import STEP_MENU

-# Путь к GIF-приветствию (в корне проекта)
-GIF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "welcome.gif")
+# Корень проекта (два рівні вгору від папки handlers)
+ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
+# Путь к GIF-приветствию (лежить у корені проєкту)
+GIF_PATH = os.path.join(ROOT_DIR, "welcome.gif")

 async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     """Обработчик /start и кнопки 'home' – присылает GIF и главное меню."""
     if update.message:
         # 1) Отправляем GIF
         with open(GIF_PATH, "rb") as gif:
             await update.message.reply_animation(gif)
         # 2) Отправляем текст и клавиатуру
         await update.message.reply_text(
             "Вітаємо у BIG GAME MONEY! Оберіть дію:",
             reply_markup=main_menu(is_admin=(update.effective_user.id == ADMIN_ID))
         )
     else:
         # пришло из callback_query (кнопка "🏠 Головне меню")
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
     """Регистрируем /start и обработчик кнопки 'home'."""
     app.add_handler(CommandHandler("start", start_command), group=0)
     app.add_handler(CallbackQueryHandler(start_command, pattern="^home$"), group=0)
