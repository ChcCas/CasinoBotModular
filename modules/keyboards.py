# modules/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .callbacks import CB

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

def nav_buttons() -> InlineKeyboardMarkup:
    """
    “Назад” та “Головне меню”
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value)],
    ])


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    """
    Головне меню: якщо адмін — кнопка «Адмін-панель», і «Головне меню»;
                 якщо клієнт — стандартні кнопки (див. client_menu(False)).
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data=CB.ADMIN_PANEL.value)],
            [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
        ])
    else:
        return client_menu(is_authorized=False)


def client_menu(is_authorized: bool) -> InlineKeyboardMarkup:
    """
    Меню клієнта (неавторизований/авторизований).
    В обох випадках кнопка «💰 Поповнити» має callback_data=CB.DEPOSIT_START.value,
    кнопка «💸 Вивести кошти» — CB.WITHDRAW_START.value.
    """
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль", callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль", callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити", callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти", callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога", callback_data=CB.HELP.value)],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",         callback_data=CB.CASHBACK.value)],
            [InlineKeyboardButton("💰 Поповнити",      callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",   callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("📖 Історія",        callback_data=CB.HISTORY.value)],
            [InlineKeyboardButton("🔒 Вийти",          callback_data=CB.LOGOUT.value)],
            [InlineKeyboardButton("ℹ️ Допомога",       callback_data=CB.HELP.value)],
        ])


def provider_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору провайдера для депозита.
    Кнопки: “🏆 CHAMPION” і “🎰 SUPEROMATIC” (callback_data точно – назва провайдера).
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)


def payment_buttons() -> InlineKeyboardMarkup:
    """
    Клавіатура вибору методу оплати / виведення.
    Кнопки: “Карта” і “Криптопереказ” (callback_data точно – назва методу).
    """
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",        callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню",  callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)


def admin_panel_kb() -> InlineKeyboardMarkup:
    """
    Клавіатура для адмін-панелі: перегляд депозитів, користувачів, виведень, статистики,
    пошук клієнта та розсилка. І внизу «Головне меню» 
    (callback_data=CB.HOME.value).
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",       callback_data=CB.ADMIN_DEPOSITS.value),
            InlineKeyboardButton("👤 Користувачі",    callback_data=CB.ADMIN_USERS.value),
        ],
        [
            InlineKeyboardButton("📄 Виведення",       callback_data=CB.ADMIN_WITHDRAWS.value),
            InlineKeyboardButton("📊 Статистика",      callback_data=CB.ADMIN_STATS.value),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",   callback_data=CB.ADMIN_SEARCH.value),
            InlineKeyboardButton("📢 Розсилка",        callback_data=CB.ADMIN_BROADCAST.value),
        ],
        [InlineKeyboardButton("🏠 Головне меню",    callback_data=CB.HOME.value)],
    ])
