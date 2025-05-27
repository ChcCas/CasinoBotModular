# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """
    Универсальные кнопки навигации: Назад и Главное меню.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


def main_menu(is_admin: bool = False, is_authorized: bool = False) -> InlineKeyboardMarkup:
    """
    Главное меню бота.
    :param is_admin: если True — показываем кнопку "Адмін-панель"
    :param is_authorized: для будущего расширения (показывать или скрывать пункты для авторизованных)
    """
    kb = [
        [InlineKeyboardButton("🎲 Мій профіль",   callback_data="client_profile")],
        [InlineKeyboardButton("📝 Реєстрація",    callback_data="register")],
        [InlineKeyboardButton("💰 Поповнити",     callback_data="deposit")],
        [InlineKeyboardButton("💸 Вивід коштів",   callback_data="withdraw")],
        [InlineKeyboardButton("ℹ️ Допомога",      callback_data="help")],
    ]

    # Опционально: если админ — показать его панель
    if is_admin:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(kb)


def provider_buttons() -> InlineKeyboardMarkup:
    """
    Кнопки выбора провайдера (для депозита через карту).
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def payment_buttons() -> InlineKeyboardMarkup:
    """
    Кнопки выбора способа оплаты.
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def client_menu(authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню клиента после авторизации (authorized=True) или перед ней (authorized=False).
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
            [InlineKeyboardButton("💳 Мій профіль",            callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку",       callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",              callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",            callback_data="withdraw")],
            [InlineKeyboardButton("🏠 Головне меню",           callback_data="home")],
        ])


def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Кнопки административной панели.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",     callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",   callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",     callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",    callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта", callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",       callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("🏠 Головне меню",   callback_data="home"),
        ],
    ])
