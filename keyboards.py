from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def nav_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
        [InlineKeyboardButton("🏠 Головне меню", callback_data="home")],
    ])

def main_menu(is_admin: bool, is_authorized: bool):
    """
    is_admin      — флаг “это админ” для показа кнопки адмін-панелі
    is_authorized — флаг “уже авторизований клієнт” для показа/скрытия кнопки Мій профіль
    """
    kb = []
    # клиентский блок
    if is_authorized:
        kb.append([InlineKeyboardButton("💳 Мій профіль", callback_data="client_profile")])
    else:
        kb.append([InlineKeyboardButton("💳 Мій профіль", callback_data="client_profile")])
    kb.append([InlineKeyboardButton("💰 Поповнити", callback_data="deposit")])
    kb.append([InlineKeyboardButton("💸 Вивід коштів", callback_data="withdraw")])
    kb.append([InlineKeyboardButton("ℹ️ Допомога", callback_data="help")])
    # адмін-панель
    if is_admin:
        kb.append([InlineKeyboardButton("🛠 Адмін-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(kb)

def client_menu(authorized: bool):
    if authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",       callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",     callback_data="deposit")],
            [InlineKeyboardButton("💸 Вивід",         callback_data="withdraw")],
            [InlineKeyboardButton("📖 Історія",       callback_data="history")],
            [InlineKeyboardButton("🔓 Вийти",         callback_data="logout")],
        ])
    else:
        # если кто-то умудрился сюда зайти без авторизации
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль", callback_data="client_profile")],
            [InlineKeyboardButton("🏠 Головне меню",callback_data="home")],
        ])

def admin_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Депозити",      callback_data="admin_deposits"),
         InlineKeyboardButton("👥 Користувачі",    callback_data="admin_users")],
        [InlineKeyboardButton("📄 Виведення",      callback_data="admin_withdrawals"),
         InlineKeyboardButton("📊 Статистика",     callback_data="admin_stats")],
        [InlineKeyboardButton("🔍 Пошук клієнта",  callback_data="admin_search"),
         InlineKeyboardButton("📢 Розсилка",      callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 Головне меню",   callback_data="home")],
    ])
