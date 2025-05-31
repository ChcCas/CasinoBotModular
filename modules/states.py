# modules/states.py

(
    STEP_MENU,                  # 0 — головне меню
    STEP_CLIENT_MENU,           # 1 — меню клієнта (якщо потрібно)
    STEP_PROFILE_ENTER_CARD,    # 2 — вводимо картку (профіль)
    STEP_PROFILE_ENTER_PHONE,   # 3 — вводимо телефон (профіль)
    STEP_PROFILE_ENTER_CODE,    # 4 — вводимо код (профіль)
    STEP_FIND_CARD_PHONE,       # 5 — вводимо ID/картку (пошук профілю)
    STEP_CLIENT_AUTH,           # 6 — клієнт авторизований

    STEP_CLIENT_CARD,           # 7 — вводимо картку (депозит)
    STEP_PROVIDER,              # 8 — вибір провайдера (депозит)
    STEP_PAYMENT,               # 9 — вибір методу оплати (депозит)

    STEP_DEPOSIT_AMOUNT,        # 10 — вводимо суму депозиту
    STEP_DEPOSIT_FILE,          # 11 — завантаження підтвердження депозиту
    STEP_DEPOSIT_CONFIRM,       # 12 — підтвердження депозиту

    STEP_WITHDRAW_AMOUNT,       # 13 — вводимо суму виведення
    STEP_WITHDRAW_METHOD,       # 14 — вибір методу виведення
    STEP_WITHDRAW_DETAILS,      # 15 — вводимо реквізити для виведення
    STEP_WITHDRAW_CONFIRM,      # 16 — підтвердження виведення

    STEP_REG_NAME,              # 17 — вводимо ім’я (реєстрація, якщо є)
    STEP_REG_PHONE,             # 18 — вводимо телефон (реєстрація, якщо є)
    STEP_REG_CODE,              # 19 — вводимо код (реєстрація, якщо є)

    STEP_ADMIN_BROADCAST,       # 20 — адміністратор: вводимо текст розсилки
    STEP_ADMIN_SEARCH,          # 21 — адміністратор: вводимо ID або картку для пошуку
    STEP_ADMIN_DEPOSITS,        # 22 — адміністратор: перегляд депозитів (за потреби)
    STEP_ADMIN_WITHDRAWALS,     # 23 — адміністратор: перегляд виведень (за потреби)
    STEP_ADMIN_USERS,           # 24 — адміністратор: перегляд користувачів (за потреби)
    STEP_ADMIN_STATS,           # 25 — адміністратор: статистика (за потреби)
) = range(26)
