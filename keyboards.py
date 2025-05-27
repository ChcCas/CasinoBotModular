# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """Універсальні кнопки «Назад» і «Головне меню»."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",        callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(authorized: bool, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Головне меню:
    - Якщо адмін (is_admin=True) — тільки одна кнопка «Адмін-панель».
    - Інакше (клієнт):
        • Мій профіль
        • Реєстрація
        • Поповнити
        • Вивід коштів (лише коли authorized=True)
        • Допомога
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")],
        ])

    kb = [
        [InlineKeyboardButton("💳 Мій профіль",    callback_data="client_profile")],
        [InlineKeyboardButton("📝 Реєстрація",     callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",      callback_data="deposit")],
    ]

    if authorized:
        kb.append([InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")])

    kb.append([InlineKeyboardButton("ℹ️ Допомога", callback_data="help")])
    return InlineKeyboardMarkup(kb)

def deposit_menu(authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню «Поповнити»:
    - Якщо авторизований → вибір провайдера.
    - Якщо ні → «Грати без карти» і «Поповнити з карткою» (запускає авторизацію).
    """
    if authorized:
        kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    else:
        kb = [
            [InlineKeyboardButton("🎮 Грати без карти",    callback_data="guest_deposit")],
            [InlineKeyboardButton("💳 Поповнити з карткою", callback_data="deposit_with_card")],
        ]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def payment_buttons() -> InlineKeyboardMarkup:
    """Меню вибору способу оплати + кнопка «Назад»."""
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню особистого кабінету:
    - authorized=True → повний набір клієнтських дій.
    - False → пропонує авторизуватися або інші базові опції.
    """
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Зняти кешбек", callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",     callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід",         callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",       callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",         callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",      callback_data="help")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",       callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку",  callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",         callback_data="deposit")],
            [InlineKeyboardButton("🏠 Головне меню",      callback_data="home")],
        ])

def admin_panel_kb() -> InlineKeyboardMarkup:
    """Клавіатура адмін-панелі з усіма опціями."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",    callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",  callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",    callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",   callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",      callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])
