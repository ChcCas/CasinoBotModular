import sqlite3

DB_NAME = "bot_data.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Таблиця реєстрацій
cursor.execute("""
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    name TEXT,
    phone TEXT,
    card TEXT,
    status TEXT DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Таблиця депозитів
cursor.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    card TEXT,
    provider TEXT,
    payment TEXT,
    file_type TEXT,
    amount TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Таблиця виведень
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    amount TEXT,
    method TEXT,
    details TEXT,
    source_code TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Таблиця threads для повідомлень
cursor.execute("""
CREATE TABLE IF NOT EXISTS threads (
    user_id INTEGER PRIMARY KEY,
    base_msg_id INTEGER
)
""")

conn.commit()
conn.close()