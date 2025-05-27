# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.db import get_user  # для перевірки авторизації

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """Універсальні кнопки «Назад» і «Головне меню»."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",        callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(user_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Головне меню для користувача або адміністратора.
    - Адмін бачить лише «Адмін-панель».
    - Клієнту:
        • Мій профіль
        • Реєстрація
        • Поповнити
        • Вивід коштів (лише якщо вже авторизований)
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

    # додаємо «Вивід» лише якщо користувач є в БД (тобто авторизований)
    if get_user(user_id):
        kb.append([InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")])

    kb.append([InlineKeyboardButton("ℹ️ Допомога", callback_data="help")])
    return InlineKeyboardMarkup(kb)

def deposit_menu(user_id: int) -> InlineKeyboardMarkup:
    """
    Підменю «Поповнити»:
    - Якщо авторизований → вибір провайдера.
    - Якщо не авторизований → два варіанти:
        • Грати без карти
        • Поповнити з карткою (запустить авторизацію)
    """
    if get_user(user_id):
        kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    else:
        kb = [
            [InlineKeyboardButton("🎮 Грати без карти", callback_data="guest_deposit")],
            [InlineKeyboardButton("💳 Поповнити з карткою", callback_data="deposit_with_card")],
        ]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def payment_buttons() -> InlineKeyboardMarkup:
    """Меню вибору способу оплати + кнопка назад."""
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню в особистому кабінеті клієнта.
    - authorized=True → повний набір дій.
    - False → пропонує авторизуватися.
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
            [InlineKeyboardButton("💳 Мій профіль",      callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку", callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",        callback_data="deposit")],
            [InlineKeyboardButton("🏠 Головне меню",     callback_data="home")],
        ])

def admin_panel_kb() -> InlineKeyboardMarkup:
    """Меню адміністратора з усіма функціями + навігація."""
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
