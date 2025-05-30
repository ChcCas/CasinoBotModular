from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .callbacks import CB

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])

def provider_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data=CB.BACK.value),
               InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)])
    return InlineKeyboardMarkup(kb)

def payment_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data=CB.BACK.value),
               InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)])
    return InlineKeyboardMarkup(kb)

def client_menu(is_authorized: bool):
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",     callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль",  callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити",       callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",   callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога",        callback_data=CB.HELP.value)],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Кешбек",          callback_data="cashback")],
        [InlineKeyboardButton("💰 Поповнити",       callback_data=CB.DEPOSIT_START.value)],
        [InlineKeyboardButton("💸 Вивести кошти",   callback_data=CB.WITHDRAW_START.value)],
        [InlineKeyboardButton("📖 Історія",         callback_data="history")],
        [InlineKeyboardButton("🔒 Вийти",           callback_data="logout")],
        [InlineKeyboardButton("ℹ️ Допомога",        callback_data=CB.HELP.value)],
    ])

def main_menu(is_admin: bool):
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель",    callback_data="admin_panel")],
            [InlineKeyboardButton("🏠 Головне меню",    callback_data=CB.HOME.value)],
        ])
    return client_menu(is_authorized=False)

def admin_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Депозити",       callback_data="admin_deposits"),
         InlineKeyboardButton("👤 Користувачі",     callback_data="admin_users")],
        [InlineKeyboardButton("📄 Виведення",      callback_data="admin_withdrawals"),
         InlineKeyboardButton("📊 Статистика",     callback_data="admin_stats")],
        [InlineKeyboardButton("🔍 Пошук клієнта",  callback_data="admin_search"),
         InlineKeyboardButton("📢 Розсилка",       callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Головне меню",   callback_data=CB.HOME.value)],
    ])
