from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def nav_buttons() -> InlineKeyboardMarkup:
    """
    Універсальні кнопки навігації:
      ◀️ Назад — повернутися на попередній крок
      🏠 Головне меню — повернутися на старт
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",    callback_data="NAV_BACK")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="NAV_HOME")],
    ])


def main_menu(is_admin: bool, is_auth: bool) -> InlineKeyboardMarkup:
    """
    Головне меню.
    
    - is_auth=False (гість):        Поповнити / Авторизуватися
    - is_auth=True  (авторизовані): Мій профіль / Поповнити / Вивід коштів
    - is_admin=True                 + кнопка Адмін-панель
    """
    kb = []

    if not is_auth:
        # Користувач не авторизований
        kb.append([InlineKeyboardButton("💰 Поповнити",      callback_data="DEPOSIT_START")])
        kb.append([InlineKeyboardButton("🔐 Авторизуватися", callback_data="PROFILE_START")])
    else:
        # Авторизований клієнт
        kb.append([InlineKeyboardButton("💳 Мій профіль",    callback_data="PROFILE_START")])
        kb.append([InlineKeyboardButton("💰 Поповнити",      callback_data="DEPOSIT_START")])
        kb.append([InlineKeyboardButton("💸 Вивід коштів",   callback_data="WITHDRAW_START")])

    if is_admin:
        # Адміністратор
        kb.append([InlineKeyboardButton("🛠 Адмін-панель",   callback_data="ADMIN_PANEL")])

    return InlineKeyboardMarkup(kb)
