# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """
    Навігаційні кнопки «Назад» і «Головне меню»,
    які можна використовувати у всіх сценаріях.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Головне меню.
    - Якщо is_admin=True, показуємо лише кнопку Адмін-панель,
      далі адміністратор переходить у меню з функціями через admin_panel_kb().
    - Інакше — стандартний набір кнопок для клієнта.
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")],
        ])

    kb = [
        [InlineKeyboardButton("🎲 КЛІЄНТ",        callback_data="client_profile")],
        [InlineKeyboardButton("📝 Реєстрація",     callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",      callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",   callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",       callback_data="help")],
    ]
    return InlineKeyboardMarkup(kb)

def provider_buttons() -> InlineKeyboardMarkup:
    """
    Меню вибору провайдера поповнення + назад/головне.
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def payment_buttons() -> InlineKeyboardMarkup:
    """
    Меню вибору способу оплати + назад/головне.
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню клієнта в залежності від авторизації.
    """
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",      callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід",        callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",      callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",        callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",     callback_data="help")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",        callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку",  callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",          callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",        callback_data="withdraw")],
            [InlineKeyboardButton("🏠 Головне меню",       callback_data="home")],
        ])

def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Меню адміна з усіма його функціями + кнопка Головне меню.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",       callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",    callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",      callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",     callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта", callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",      callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню",   callback_data="home")],
    ])
