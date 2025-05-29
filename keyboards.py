# src/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]


def nav_buttons() -> InlineKeyboardMarkup:
    """Кнопки «Назад» і «Головне меню»"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",       callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


def provider_buttons() -> InlineKeyboardMarkup:
    """Кнопки вибору провайдера"""
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def payment_buttons() -> InlineKeyboardMarkup:
    """Кнопки вибору способу оплати"""
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def client_menu(is_authorized: bool) -> InlineKeyboardMarkup:
    """
    Головне меню для користувача:
    якщо авторизований – показує додаткові кнопки,
    якщо ні – базове меню з «Мій профіль».
    """
    if is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Зняти кешбек",    callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",       callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",    callback_data="WITHDRAW_START")],
            [InlineKeyboardButton("📖 Історія",         callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти з профілю", callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",        callback_data="help")],
            [InlineKeyboardButton("🏠 Головне меню",    callback_data="home")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",      callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку", callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",        callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",      callback_data="WITHDRAW_START")],
            [InlineKeyboardButton("ℹ️ Допомога",         callback_data="help")],
            [InlineKeyboardButton("🏠 Головне меню",     callback_data="home")],
        ])


def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    """
    Головне меню /start:
    якщо адмін – тільки кнопка до адмін-панелі,
    якщо користувач – показує «Мій профіль» і далі.
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",      callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку", callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",        callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід коштів",      callback_data="WITHDRAW_START")],
            [InlineKeyboardButton("ℹ️ Допомога",         callback_data="help")],
            [InlineKeyboardButton("🏠 Головне меню",     callback_data="home")],
        ])


def admin_panel_kb() -> InlineKeyboardMarkup:
    """Меню адмін-панелі (не змінюємо)"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",    callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",    callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",   callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта", callback_data="admin_search"),
            InlineKeyboardButton("📢 Розсилка",      callback_data="admin_broadcast"),
        ],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])