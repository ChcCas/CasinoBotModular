# states.py

(
    STEP_MENU,                    # 0
    STEP_CLIENT_MENU,             # 1
    STEP_PROFILE_ENTER_CARD,      # 2
    STEP_PROFILE_ENTER_PHONE,     # 3
    STEP_PROFILE_ENTER_CODE,      # 4
    STEP_FIND_CARD_PHONE,         # 5
    STEP_CLIENT_AUTH,             # 6

    # Новые станы для "guest deposit"
    STEP_GUEST_DEPOSIT,           # 7   – "Грати без карти"
    STEP_GUEST_DEPOSIT_PROVIDER,  # 8
    STEP_GUEST_DEPOSIT_PAYMENT,   # 9
    STEP_GUEST_DEPOSIT_AMOUNT,    # 10
    STEP_GUEST_DEPOSIT_CONFIRM,   # 11
    STEP_GUEST_DEPOSIT_CODE,      # 12

    # Обычные депозит/вывод–стадии
    STEP_PROVIDER,                # 13
    STEP_PAYMENT,                 # 14
    STEP_DEPOSIT_AMOUNT,          # 15
    STEP_CONFIRM_FILE,            # 16
    STEP_CONFIRMATION,            # 17

    STEP_WITHDRAW_AMOUNT,         # 18
    STEP_WITHDRAW_METHOD,         # 19
    STEP_WITHDRAW_DETAILS,        # 20
    STEP_WITHDRAW_CONFIRM,        # 21

    # Регистрация
    STEP_REG_NAME,                # 22
    STEP_REG_PHONE,               # 23
    STEP_REG_CODE,                # 24

    # Админские сценарии
    STEP_ADMIN_BROADCAST,         # 25
    STEP_ADMIN_SEARCH,            # 26

    # остаточный
) = range(27)
