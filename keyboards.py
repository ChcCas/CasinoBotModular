from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]


def nav_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])


def provider_buttons() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def payment_buttons() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Головне меню", callback_data="home"),
    ])
    return InlineKeyboardMarkup(kb)


def main_menu(is_admin: bool, is_auth: bool = False) -> InlineKeyboardMarkup:
    """
    Головне меню. Якщо is_admin=True — адмінка, 
    інакше клієнтське (з урахуванням авторизації).
    """
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")],
            [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
        ])

    # --- меню клієнта ---
    if is_auth:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Зняти кешбек", callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",     callback_data="DEPOSIT_START")],
            [InlineKeyboardButton("💸 Вивід коштів",  callback_data="WITHDRAW_START")],
            [InlineKeyboardButton("📖 Історія",       callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",         callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",      callback_data="help")],
            [InlineKeyboardButton("🏠 Головне меню",  callback_data="home")],
        )]
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",       callback_data="client_profile")],
            [InlineKeyboardButton("📇 Дізнатися картку",  callback_data="client_find_card")],
            [InlineKeyboardButton("💰 Поповнити",         callback_data="DEPOSIT_START")],
            [InlineKeyboardButton("💸 Вивід коштів",      callback_data="WITHDRAW_START")],
            [InlineKeyboardButton("🏠 Головне меню",      callback_data="home")],
        ])