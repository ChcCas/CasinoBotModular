# src/modules/states.py

# Чёткий список всех состояний диалогов
(
    STEP_MENU,                  # 0 — главное меню
    STEP_CLIENT_MENU,           # 1 — меню клиента
    STEP_PROFILE_ENTER_CARD,    # 2 — ввод номера карты (профиль)
    STEP_PROFILE_ENTER_PHONE,   # 3 — ввод телефона (профиль)
    STEP_PROFILE_ENTER_CODE,    # 4 — ввод кода (профиль)
    STEP_FIND_CARD_PHONE,       # 5 — ввод ID/карты для поиска
    STEP_CLIENT_AUTH,           # 6 — клиент успешно авторизован

    STEP_CLIENT_CARD,           # 7 — ввод карты (депозит)
    STEP_PROVIDER,              # 8 — выбор провайдера (депозит)
    STEP_PAYMENT,               # 9 — выбор платежа (депозит)

    STEP_DEPOSIT_AMOUNT,        # 10 — ввод суммы депозита
    STEP_DEPOSIT_FILE,          # 11 — загрузка файла подтверждения депозита
    STEP_DEPOSIT_CONFIRM,       # 12 — подтверждение депозита

    STEP_WITHDRAW_AMOUNT,       # 13 — ввод суммы вывода
    STEP_WITHDRAW_METHOD,       # 14 — выбор метода вывода
    STEP_WITHDRAW_DETAILS,      # 15 — ввод реквизитов
    STEP_WITHDRAW_CONFIRM,      # 16 — подтверждение вывода

    STEP_REG_NAME,              # 17 — ввод имени (регистрация)
    STEP_REG_PHONE,             # 18 — ввод телефона (регистрация)
    STEP_REG_CODE,              # 19 — ввод кода (регистрация)

    STEP_ADMIN_BROADCAST,       # 20 — админ: рассылка
    STEP_ADMIN_SEARCH,          # 21 — админ: поиск пользователя
    STEP_ADMIN_DEPOSITS,        # 22 — админ: просмотр депозитов
    STEP_ADMIN_WITHDRAWALS,     # 23 — админ: просмотр выводов
    STEP_ADMIN_USERS,           # 24 — админ: просмотр пользователей
    STEP_ADMIN_STATS,           # 25 — админ: статистика
) = range(26)
