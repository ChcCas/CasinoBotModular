# modules/states.py

(
    STEP_MENU,              # 0   — загальна точка повернення (якщо потрібна)
    STEP_FIND_CARD_PHONE,   # 1   — “Мій профіль”: крок введення номера картки
    STEP_DEPOSIT_AMOUNT,    # 2   — “Депозит”: крок введення суми
    STEP_DEPOSIT_PROVIDER,  # 3   — “Депозит”: вибір провайдера
    STEP_DEPOSIT_PAYMENT,   # 4   — “Депозит”: вибір методу оплати
    STEP_DEPOSIT_FILE,      # 5   — “Депозит”: надсилання фото/документа
    STEP_DEPOSIT_CONFIRM,   # 6   — “Депозит”: підтвердження операції
    STEP_WITHDRAW_AMOUNT,   # 7   — “Виведення”: крок введення суми
    STEP_WITHDRAW_METHOD,   # 8   — “Виведення”: вибір методу виведення
    STEP_WITHDRAW_DETAILS,  # 9   — “Виведення”: введення реквізитів/деталей
    STEP_WITHDRAW_CONFIRM,  # 10  — “Виведення”: підтвердження операції
    STEP_REG_NAME,          # 11  — “Реєстрація”: крок введення імені
    STEP_REG_PHONE,         # 12  — “Реєстрація”: крок введення телефону
    STEP_REG_CODE,          # 13  — “Реєстрація”: крок введення коду підтвердження
    STEP_ADMIN_SEARCH,      # 14  — “Адмін”: крок введення ID/картки для пошуку
    STEP_ADMIN_BROADCAST    # 15  — “Адмін”: крок введення тексту для розсилки
) = range(16)
