# states.py

(
    STEP_MENU,
    STEP_CLIENT_MENU,
    STEP_PROFILE_ENTER_CARD,
    STEP_PROFILE_ENTER_PHONE,
    STEP_PROFILE_ENTER_CODE,
    STEP_FIND_CARD_PHONE,
    STEP_CLIENT_AUTH,
    # нові стани для поповнення:
    STEP_GUEST_DEPOSIT,          # кнопка "Грати без карти"
    STEP_GUEST_DEPOSIT_PROVIDER, # вибір провайдера для гостя
    STEP_GUEST_DEPOSIT_PAYMENT,  # вибір способу оплати для гостя
    STEP_GUEST_DEPOSIT_AMOUNT,   # введення суми гостем
    STEP_GUEST_DEPOSIT_CONFIRM,  # підтвердження файлу/суми гостем
    STEP_GUEST_DEPOSIT_CODE,     # введення коду sms гостем
    # далі ваші вже існуючі:
    STEP_PROVIDER,
    STEP_PAYMENT,
    STEP_DEPOSIT_AMOUNT,
    STEP_CONFIRM_FILE,
    STEP_CONFIRMATION,
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,
    STEP_ADMIN_BROADCAST,
    STEP_ADMIN_SEARCH,
) = range(28)
