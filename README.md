# Casino Telegram Bot (Flask + Webhook)

Це Telegram-бот для обслуговування клієнтів казино, написаний на Python з використанням Flask + python-telegram-bot v20.

## Особливості

- Webhook логіка через Flask
- Повністю асинхронна обробка повідомлень
- Модульна структура для масштабування
- Збереження користувачів у SQLite
- Обробка натискань кнопок (inline)
- Підтримка деплою на Render/Heroku

---

## Структура проєкту

```
.
├── main.py
├── modules/
│   ├── config.py
│   ├── db.py
│   ├── handlers.py
│   └── routes.py
├── .env.example
├── requirements.txt
└── Procfile
```

---

## Як запустити локально

1. Клонуйте репозиторій:
```bash
git clone https://github.com/yourname/CasinoBot.git
cd CasinoBot
```

2. Створіть `.env` файл на основі `.env.example`:
```bash
cp .env.example .env
```

3. Встановіть залежності:
```bash
pip install -r requirements.txt
```

4. Запустіть бота:
```bash
python main.py
```

---

## Деплой на Render

1. Завантажте код у GitHub.
2. Створіть новий Web Service на [render.com](https://render.com).
3. Додайте змінні середовища:
    - `TOKEN`
    - `WEBHOOK_URL` (https://your-service-name.onrender.com/webhook)
    - `ADMIN_ID`
    - `PORT` = 5000

4. Після запуску відкрий `/set-webhook` в браузері:
```
https://your-app.onrender.com/set-webhook
```

---

## Ліцензія

MIT License
