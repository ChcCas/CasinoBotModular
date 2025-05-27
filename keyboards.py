# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons():
    """Кнопки навігації: Назад і Головне меню."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(is_admin: bool = False):
    """
    Головне меню.
    - якщо адмін — додається кнопка Адмін-панель.
    - для всіх — кнопка Мій профіль, Реєстрація, Поповнити, Вивід, Поміч.
    """
    kb = [
        [InlineKeyboardButton("💳 Мій профіль",    callback_data="client_profile")],
        [InlineKeyboardButton("📝 Реєстрація",     callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",      callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",    callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",       callback_data="help")],
    ]
    if is_admin:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def deposit_menu(authorized: bool):
    """
    Меню поповнення.
    - авторизовані: без додаткових варіантів, показує провайдери.
    - не авторизовані: додає кнопку «Грати без карти».
    """
    kb = []
    if not authorized:
        kb.append([InlineKeyboardButton("🎮 Грати без карти", callback_data="guest_deposit")])
    # вибір провайдера
    for p in PROVIDERS:
        kb.append([InlineKeyboardButton(p, callback_data=f"prov|{p}")])
    # назад/домів
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def payment_menu():
    """Меню вибору способу оплати."""
    kb = [[InlineKeyboardButton(p, callback_data=f"pay|{p}")] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool):
    """
    Меню профілю після авторизації.
    - авторизовані: кешбек, поповнити, вивід, історія, вийти, допомога.
    - не авторизовані: авторизація через картку, дізнатися картку, поповнити, вивід, домів.
    """
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Зняти кешбек", callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід",         callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",       callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",         callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",      callback_data="help")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",               callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися номер картки",    callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",                 callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",               callback_data="withdraw")],
            [InlineKeyboardButton("🏠 Головне меню",              callback_data="home")],
        ])

def admin_panel_kb():
    """Клавіатура адмін-панелі."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",    callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",  callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",   callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",  callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта", callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",      callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
