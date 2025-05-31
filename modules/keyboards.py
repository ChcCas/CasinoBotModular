# modules/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .callbacks import CB

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """
    Загальна клавіатура “Назад / Головне меню”
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value)],
    ])


def provider_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору провайдера (для депозиту).
    Кнопки: назви зі списку PROVIDERS, потім “Назад” і “Головне меню”.
    """
    # Для кожного провайдера ми передаємо callback_data == сама назва провайдера,
    # наприклад "🏆 CHAMPION" або "🎰 SUPEROMATIC". У хендлері депозиту ми на це
    # дивимось (у коді deposit.py).
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)


def payment_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору методу оплати або виведення.
    Кнопки: назви зі списку PAYMENTS, потім “Назад” і “Головне меню”.
    """
    # Тут ми використовуємо ті самі рядки, що й у списку PAYMENTS:
    # "Карта" або "Криптопереказ". У хендлері депозиту / виведення
    # вони мають чекати саме ці значення (pattern="^Карта$|^Криптопереказ$")
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)


def client_menu(is_authorized: bool) -> InlineKeyboardMarkup:
    """
    Головне меню клієнта:
      — якщо не авторизований: показуємо кнопки “Мій профіль”, “Знайти профіль”,
        “Поповнити”, “Вивести кошти”, “Допомога”.
      — якщо авторизований: показуємо додаткові кнопки, у тому числі повторно
        “Поповнити” та “Вивести кошти”.
    """
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",       callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль",     callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити",         callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",      callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога",          callback_data=CB.HELP.value)],
        ])
    else:
        # Якщо користувач вже авторизований, тут можна відобразити інші дії.
        # Наприклад, кешбек, історію, вихід і т.д. Ми лишили “Поповнити” та “Вивести кошти”
        # з тими самими callback_data.
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",            callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",         callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",      callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("📖 Історія",           callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",             callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",          callback_data=CB.HELP.value)],
        ])


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    """
    Головне меню для /start або “Головне меню”:
      — якщо адмін: показує тільки кнопку “Адмін-панель” і “Головне меню”;
      — інакше: передаємо стандартне client_menu(is_authorized=False).
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
    Клавіатура для адмін-панелі:
      — кнопки перегляду депозитів, користувачів, виведень, статистики,
        пошуку клієнта та розсилки.
      — потім “Головне меню”.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",       callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",    callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",       callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",      callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",   callback_data=CB.ADMIN_SEARCH.value),
            InlineKeyboardButton("📢 Розсилка",        callback_data=CB.ADMIN_BROADCAST.value),
        ],
        [InlineKeyboardButton("🏠 Головне меню",    callback_data=CB.HOME.value)],
    ])
