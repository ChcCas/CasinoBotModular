# modules/callbacks.py

from enum import Enum

class CB(Enum):
    # ─── Навігаційні дії ───
    HOME             = "home"             # «🏠 Головне меню»
    BACK             = "back"             # «◀️ Назад»
    HELP             = "help"             # «ℹ️ Допомога»
    REGISTER         = "register"         # «📝 Реєстрація» (якщо потрібна окрема кнопка)

    # ─── Профіль клієнта ───
    CLIENT_PROFILE   = "client_profile"   # «💳 Мій профіль»
    CLIENT_FIND      = "client_find"      # «🔍 Знайти профіль»

    # ─── Депозит ───
    DEPOSIT_START    = "deposit_start"    # «💰 Поповнити»
    DEPOSIT_AMOUNT   = "deposit_amount"   # (крок вводу суми)
    DEPOSIT_PROVIDER = "deposit_provider" # (крок вибору провайдера)
    DEPOSIT_PAYMENT  = "deposit_payment"  # (крок вибору методу оплати)
    DEPOSIT_FILE     = "deposit_file"     # (крок надсилання фото/документа)
    DEPOSIT_CONFIRM  = "deposit_confirm"  # (кнопка «Підтвердити» для депозиту)

    # ─── Виведення ───
    WITHDRAW_START   = "withdraw_start"   # «💸 Вивести кошти»
    WITHDRAW_AMOUNT  = "withdraw_amount"  # (крок вводу суми)
    WITHDRAW_METHOD  = "withdraw_method"  # (крок вибору методу виведення)
    WITHDRAW_DETAILS = "withdraw_details" # (крок вводу деталей/реквізитів)
    WITHDRAW_CONFIRM = "withdraw_confirm" # (кнопка «Підтвердити» для виведення)

    # ─── Адмінські дії ───
    ADMIN_PANEL      = "admin_panel"      # «🛠 Адмін-панель»
    ADMIN_DEPOSITS   = "admin_deposits"   # «💰 Депозити»
    ADMIN_USERS      = "admin_users"      # «👤 Користувачі»
    ADMIN_WITHDRAWS  = "admin_withdrawals"# «📄 Виведення»
    ADMIN_STATS      = "admin_stats"      # «📊 Статистика»
    ADMIN_SEARCH     = "admin_search"     # «🔍 Пошук клієнта»
    ADMIN_BROADCAST  = "admin_broadcast"  # «📢 Розсилка»

    # ─── Інші дії (якщо потрібні) ───
    LOGOUT           = "logout"           # «🔒 Вийти»
    HISTORY          = "history"          # «📖 Історія»
    CASHBACK         = "cashback"         # «🎁 Кешбек»
