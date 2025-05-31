from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from modules.callbacks import CB

# Для депозиту/виведення: відображені назви провайдерів
PROVIDERS = ["СТАРА СИСТЕМА", "НОВА СИСТЕМА"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """
    “◀️ Назад” / “🏠 Головне меню”
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])

def provider_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору провайдера (для депозиту),
    відображає “СТАРА СИСТЕМА”/“НОВА СИСТЕМА”.
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)

def payment_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору методу оплати / виведення.
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)

def client_menu(is_authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню для клієнта:
    - Якщо is_authorized=False → кнопки “Мій профіль”, “Знайти профіль”, “Поповнити”, “Вивести кошти”, “Допомога”.
    - Якщо is_authorized=True → кнопки “Кешбек”, “Поповнити”, “Вивести кошти”, “Історія”, “Вийти”, “Допомога”.
    """
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",      callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль",    callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити",        callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",     callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога",         callback_data=CB.HELP.value)],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",           callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",        callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",     callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("📖 Історія",          callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",            callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",         callback_data=CB.HELP.value)],
        ])

def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    """
    Головне меню (при /start):
    - Якщо is_admin=True → показуємо клавіатуру адміна.
    - Інакше → показуємо меню неавторизованого клієнта.
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель",    callback_data="admin_panel")],
            [InlineKeyboardButton("🏠 Головне меню",    callback_data=CB.HOME.value)],
        ])
    else:
        return client_menu(is_authorized=False)

def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Клавіатура адмін-панелі: депозити, користувачі, виведення, статистика, пошук, розсилка.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",        callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",     callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",        callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",       callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",    callback_data=CB.ADMIN_SEARCH.value),
            InlineKeyboardButton("📢 Розсилка",         callback_data=CB.ADMIN_BROADCAST.value),
        ],
        [InlineKeyboardButton("🏠 Головне меню",     callback_data=CB.HOME.value)],
    ])
