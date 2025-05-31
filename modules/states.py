# modules/states.py

(
    # ─── Головне меню (за замовчуванням) ───
    STEP_MENU,

    # ─── Сценарій «Мій профіль» ───
    STEP_FIND_CARD_PHONE,

    # ─── Сценарій «Знайти профіль» (якщо окремо) ───
    STEP_FIND_PROFILE_PHONE,

    # ─── Сценарій депозиту ───
    STEP_DEPOSIT_AMOUNT,
    STEP_DEPOSIT_PROVIDER,
    STEP_DEPOSIT_PAYMENT,
    STEP_DEPOSIT_FILE,
    STEP_DEPOSIT_CONFIRM,

    # ─── Сценарій виведення ───
    STEP_WITHDRAW_AMOUNT,
    STEP_WITHDRAW_METHOD,
    STEP_WITHDRAW_DETAILS,
    STEP_WITHDRAW_CONFIRM,

    # ─── Сценарій реєстрації ───
    STEP_REG_NAME,
    STEP_REG_PHONE,
    STEP_REG_CODE,

    # ─── Адмінські сценарії ───
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST

) = range(16)
