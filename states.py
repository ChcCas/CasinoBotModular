# states.py

# 0: главное меню
STEP_MENU = 0

# 1: профиль клиента
STEP_CLIENT_MENU = 1

# === сценарий "Мій профіль" ===
STEP_PROFILE_ENTER_CARD   = 2  # ввод номера карты
STEP_PROFILE_ENTER_PHONE  = 3  # ввод телефона
STEP_PROFILE_ENTER_CODE   = 4  # ввод SMS-кода

# === сценарий "Знайти картку" (если есть) ===
STEP_FIND_CARD_PHONE      = 5

# === сценарий авторизации клиента ===
STEP_CLIENT_AUTH          = 6
STEP_CLIENT_CARD          = 7

# === гость без карты: поповнення ===
STEP_GUEST_DEPOSIT_FILE    = 8   # загрузка скриншота/файла
STEP_GUEST_DEPOSIT_CONFIRM = 9   # подтверждение отправки

# === обычный депозит/вивід ===
STEP_PROVIDER             = 10
STEP_PAYMENT              = 11
STEP_DEPOSIT_AMOUNT       = 12
STEP_CONFIRM_FILE         = 13
STEP_CONFIRMATION         = 14

STEP_WITHDRAW_AMOUNT      = 15
STEP_WITHDRAW_METHOD      = 16
STEP_WITHDRAW_DETAILS     = 17
STEP_WITHDRAW_CONFIRM     = 18

# === реєстрація ===
STEP_REG_NAME             = 19
STEP_REG_PHONE            = 20
STEP_REG_CODE             = 21

# === адмінські сценарії ===
STEP_ADMIN_BROADCAST      = 22
STEP_ADMIN_SEARCH         = 23

# если потом добавите что-то ещё, просто увеличьте до нужного числа
# здесь у нас 24 состояния (0..23), поэтому range = 24
__all_states__ = 24
STATE_RANGE = range(__all_states__)
