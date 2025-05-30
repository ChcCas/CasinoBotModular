# modules/callbacks.py

from enum import Enum

class CB(Enum):
    # Навігація
    HOME = "home"
    BACK = "back"

    # Профіль клієнта
    CLIENT_PROFILE = "client_profile"
    CLIENT_FIND    = "client_find"

    # Початок сценаріїв депозиту/виведення
    DEPOSIT_START  = "deposit_start"
    WITHDRAW_START = "withdraw_start"

    # Сценарій депозиту
    DEPOSIT_AMOUNT  = "deposit_amount"
    DEPOSIT_FILE    = "deposit_file"
    DEPOSIT_CONFIRM = "deposit_confirm"

    # Сценарій виведення
    WITHDRAW_AMOUNT  = "withdraw_amount"
    WITHDRAW_METHOD  = "withdraw_method"
    WITHDRAW_DETAILS = "withdraw_details"
    WITHDRAW_CONFIRM = "withdraw_confirm"

    # Додаткові дії
    HELP = "help"
