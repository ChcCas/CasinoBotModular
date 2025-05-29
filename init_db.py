import sqlite3

DB_NAME = "bot_data.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Додаємо стовпець card до таблиці registrations, якщо його ще немає
try:
    cursor.execute("ALTER TABLE registrations ADD COLUMN card TEXT")
    print("✅ Стовпець 'card' успішно додано.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ Стовпець 'card' вже існує — пропускаємо.")
    else:
        raise

conn.commit()
conn.close()