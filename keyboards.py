# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons():
    """Кнопки навігації: Назад / Головне меню."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(is_admin: bool = False, is_authorized: bool = False):
    """
    Головне меню:
    - Якщо клієнт не авторизований: показує кнопку '🎲 Поповнити' веде в гостевий флоу,
      а також дає можливість зареєструватися.
    - Якщо клієнт авторизований: замість реєстрації – кнопки депозит/вивід тощо.
    - Якщо адмін: додається кнопка '🛠 Адмін-панель'.
    """
    kb = []

    # пункт "Мій профіль" — доступний лише авторизованим
    if is_authorized:
        kb.append([InlineKeyboardButton("🎲 МІЙ ПРОФІЛЬ", callback_data="client_profile")])
    else:
        # для незалогінених: пропонуємо гостеве поповнення або зареєструватись
        kb.append([InlineKeyboardButton("🎮 Грати без карти", callback_data="guest_deposit")])
        kb.append([InlineKeyboardButton("📝 Реєстрація", callback_data="register")])

    # для всіх: допомога та вихід
    kb.append([InlineKeyboardButton("ℹ️ Допомога", callback_data="help")])

    # для авторизованих: депозит / вивід / кешбек / історія / вихід
    if is_authorized:
        kb.insert(1, [InlineKeyboardButton("💰 Поповнити", callback_data="deposit")])
        kb.insert(2, [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")])
        kb.insert(3, [InlineKeyboardButton("🎁 Зняти кешбек", callback_data="cashback")])
        kb.insert(4, [InlineKeyboardButton("📖 Історія", callback_data="history")])
        kb.insert(5, [InlineKeyboardButton("🔒 Вийти", callback_data="logout")])

    # якщо адмін — додаємо в кінець адмін-панель
    if is_admin:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(kb)

def provider_buttons():
    """Вибір провайдера (депозит/гостьовий)."""
    kb = [[InlineKeyboardButton(text=p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",      callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def payment_buttons():
    """Вибір способу оплати."""
    kb = [[InlineKeyboardButton(text=p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",      callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool):
    """Кабінет клієнта після авторизації."""
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Зняти кешбек", callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",    callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",      callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",        callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",     callback_data="help")],
        ])
    else:
        # Незалогінений бачить тільки реєстрацію/гостьовий флоу
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",           callback_data="client_profile")],
            [InlineKeyboardButton("🎮 Поповнити без карти",   callback_data="guest_deposit")],
            [InlineKeyboardButton("🏠 Головне меню",          callback_data="home")],
        ])

def admin_panel_kb():
    """Меню адміністратора."""
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
        [
            InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
        ],
    ])
