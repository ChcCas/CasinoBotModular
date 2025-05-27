# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(is_admin=False):
    kb = [
        [InlineKeyboardButton("🎲 КЛІЄНТ",    callback_data="client_profile")],
        [InlineKeyboardButton("📝 Реєстрація", callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",  callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",   callback_data="help")],
    ]
    if is_admin:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def provider_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    return InlineKeyboardMarkup(kb)

def payment_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back"),
               InlineKeyboardButton("🏠 Головне меню", callback_data="home")])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool):
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",  callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід",    callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",  callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",    callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога", callback_data="help")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку",callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",        callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",      callback_data="withdraw")],
            [InlineKeyboardButton("🏠 Головне меню",      callback_data="home")],
        ])

def admin_panel_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",   callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення", callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",     callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню",callback_data="home")],
    ])
