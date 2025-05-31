# modules/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .callbacks import CB

# ─── Списки для депозиту/виведення ────────────────────────────────────────────────
PROVIDERS = ["🏆 CHAMPION", "🎰 SUPEROMATIC"]
PAYMENTS  = ["Карта", "Криптопереказ"]

# ─── Клавіатура “Назад” / “Головне меню” ────────────────────────────────────────
def nav_buttons():
    """
    Універсальна клавіатура “Назад” та “Головне меню”.
    Використовується в усіх кроках, де треба дозволити повернутися назад або в головне меню.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value)],
        [InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value)],
    ])

# ─── Клавіатура вибору провайдера (для депозиту) ───────────────────────────────
def provider_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PROVIDERS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)

# ─── Клавіатура вибору методу оплати / виведення ────────────────────────────────
def payment_buttons():
    kb = [[InlineKeyboardButton(p, callback_data=p)] for p in PAYMENTS]
    kb.append([
        InlineKeyboardButton("◀️ Назад",       callback_data=CB.BACK.value),
        InlineKeyboardButton("🏠 Головне меню", callback_data=CB.HOME.value),
    ])
    return InlineKeyboardMarkup(kb)

# ─── Клавіатура клієнтського меню ────────────────────────────────────────────────
def client_menu(is_authorized: bool):
    """
    Клавіатура, яка показується звичайному користувачеві (не-адміну).
    Якщо is_authorized == False — пропонуємо увійти через картку.
    Якщо is_authorized == True  — показуємо “Кешбек”, “Поповнити” тощо.
    """
    if not is_authorized:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Мій профіль",        callback_data=CB.CLIENT_PROFILE.value)],
            [InlineKeyboardButton("🔍 Знайти профіль",      callback_data=CB.CLIENT_FIND.value)],
            [InlineKeyboardButton("💰 Поповнити",          callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",       callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("ℹ️ Допомога",           callback_data=CB.HELP.value)],
        ])
    else:
        # Коли клієнт уже авторизований (після підтвердження картки)
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Кешбек",             callback_data="cashback")],
            [InlineKeyboardButton("💰 Поповнити",          callback_data=CB.DEPOSIT_START.value)],
            [InlineKeyboardButton("💸 Вивести кошти",       callback_data=CB.WITHDRAW_START.value)],
            [InlineKeyboardButton("📖 Історія",            callback_data="history")],
            [InlineKeyboardButton("🔒 Вийти",              callback_data="logout")],
            [InlineKeyboardButton("ℹ️ Допомога",           callback_data=CB.HELP.value)],
        ])

# ─── Головне меню (якщо is_admin=True, показуємо адмін-панель; інакше — клієнтське) ─
def main_menu(is_admin: bool):
    if is_admin:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Адмін-панель",      callback_data="admin_panel")],
            [InlineKeyboardButton("🏠 Головне меню",      callback_data=CB.HOME.value)],
        ])
    else:
        return client_menu(is_authorized=False)

# ─── Клавіатура адмін-панелі ────────────────────────────────────────────────────
def admin_panel_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Депозити",       callback_data="admin_deposits"),
            InlineKeyboardButton("👤 Користувачі",    callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📄 Виведення",      callback_data="admin_withdrawals"),
            InlineKeyboardButton("📊 Статистика",     callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 Пошук клієнта",  callback_data=CB.ADMIN_SEARCH.value),
            InlineKeyboardButton("📢 Розсилка",       callback_data=CB.ADMIN_BROADCAST.value),
        ],
        [
            InlineKeyboardButton("🏠 Головне меню",   callback_data=CB.HOME.value),
        ],
    ])
