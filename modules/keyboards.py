from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .callbacks import CB

def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])

def client_menu(is_authorized: bool):
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль", callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль", callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити",     callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти", callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога",      callback_data=CB.HELP.value)],
        ])
    # якщо авторизовано — додаємо кешбек, історію, логаут тощо
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Кешбек",       callback_data="cashback")],
        [InlineKeyboardButton("💰 Поповнити",     callback_data=CB.DEPOSIT_START.value)],
        [InlineKeyboardButton("💸 Вивести кошти", callback_data=CB.WITHDRAW_START.value)],
        [InlineKeyboardButton("📖 Історія",       callback_data="history")],
        [InlineKeyboardButton("🔒 Вийти",         callback_data="logout")],
        [InlineKeyboardButton("ℹ️ Допомога",      callback_data=CB.HELP.value)],
    ])
