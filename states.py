# states.py

"""
Перелік всіх станів (steps) для ConversationHandler.
"""

(
    STEP_MENU,                      # 0 – головне меню / старт
    STEP_CLIENT_MENU,               # 1 – меню клієнта після авторизації
    STEP_PROFILE_ENTER_CARD,        # 2 – профіль: введення номера картки
    STEP_PROFILE_ENTER_PHONE,       # 3 – профіль: введення номера телефону
    STEP_PROFILE_ENTER_CODE,        # 4 – профіль: введення коду підтвердження реєстрації
    STEP_PROFILE_CASHBACK_REQUEST,  # 5 – профіль: запит кешбеку (натиск кешбек)
    STEP_PROFILE_CASHBACK_CODE,     # 6 – профіль: введення коду для кешбеку
    STEP_FIND_CARD_PHONE,           # 7 – дізнатися картку: введення номера телефону
    STEP_CLIENT_AUTH,               # 8 – авторизація клієнта (введення картки+телефону)
    STEP_CLIENT_CARD,               # 9 – поповнення: введення номера картки клієнта
    STEP_PROVIDER,                  # 10 – поповнення: вибір провайдера
    STEP_PAYMENT,                   # 11 – поповнення/вивід: вибір способу оплати
    STEP_DEPOSIT_AMOUNT,            # 12 – поповнення: введення суми (за бажанням)
    STEP_CONFIRM_FILE,              # 13 – поповнення/вивід: очікування файлу підтвердження
    STEP_CONFIRMATION,              # 14 – поповнення/вивід: підтвердження надсилання
    STEP_WITHDRAW_AMOUNT,           # 15 – вивід: введення суми
    STEP_WITHDRAW_METHOD,           # 16 – вивід: вибір способу
    STEP_WITHDRAW_DETAILS,          # 17 – вивід: введення деталей/реквізитів (якщо є)
    STEP_WITHDRAW_CONFIRM,          # 18 – вивід: підтвердження заявки
    STEP_REG_NAME,                  # 19 – реєстрація: введення імені
    STEP_REG_PHONE,                 # 20 – реєстрація: введення телефону
    STEP_REG_CODE,                  # 21 – реєстрація: введення коду підтвердження
    STEP_ADMIN_BROADCAST,           # 22 – адмін: введення тексту для розсилки
    STEP_ADMIN_SEARCH,              # 23 – адмін: введення ID для пошуку клієнта
) = range(24)
