# modules/handlers/admin.py

import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters
from modules.config import ADMIN_ID, DB_NAME
from keyboards     import admin_panel_kb, nav_buttons
from states        import (
    STEP_MENU,
    STEP_ADMIN_SEARCH,
    STEP_ADMIN_BROADCAST,
)

# ————— Адмін-панель —————————————————————
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Панель адміністратора:", reply_markup=admin_panel_kb()
    )
    return STEP_MENU

async def admin_deposits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = sqlite3.connect(DB_NAME).execute(
        "SELECT username, card, provider, payment, timestamp FROM deposits ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    text = "\n\n".join(
        f"👤 {r[0]}\nКартка: {r[1]}\nПровайдер: {r[2]}\nОплата: {r[3]}\n🕒 {r[4]}"
        for r in rows or [("—","—","—","—","—")]
    )
    await update.callback_query.message.reply_text(f"Останні депозити:\n\n{text}", reply_markup=nav_buttons())
    return STEP_MENU

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = sqlite3.connect(DB_NAME).execute(
        "SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10"
    ).fetchall()
    text = "\n\n".join(
        f"👤 {r[0]}\n📞 {r[1]}\nСтатус: {r[2]}"
        for r in rows or [("—","—","—")]
    )
    await update.callback_query.message.reply_text(f"Зареєстровані користувачі:\n\n{text}", reply_markup=nav_buttons())
    return STEP_MENU

async def admin_withdrawals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    rows = sqlite3.connect(DB_NAME).execute(
        "SELECT username, amount, method, details, timestamp FROM withdrawals ORDER BY id DESC LIMIT 10"
    ).fetchall()
    text = "\n\n".join(
        f"👤 {r[0]}\n💸 {r[1]}\nМетод: {r[2]}\nРеквізити: {r[3]}\n🕒 {r[4]}"
        for r in rows or [("—",0,"—","—","—")]
    )
    await update.callback_query.message.reply_text(f"Заявки на виведення:\n\n{text}", reply_markup=nav_buttons())
    return STEP_MENU

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    conn = sqlite3.connect(DB_NAME)
    users = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    deps  = conn.execute("SELECT COUNT(*) FROM deposits").fetchone()[0]
    wds   = conn.execute("SELECT COUNT(*) FROM withdrawals").fetchone()[0]
    await update.callback_query.message.reply_text(
        f"📊 Статистика:\nКористувачів: {users}\nДепозитів: {deps}\nВиведень: {wds}", 
        reply_markup=nav_buttons()
    )
    return STEP_MENU

# ————— Пошук клієнта —————————————————————
async def admin_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введіть ID клієнта для пошуку:", reply_markup=nav_buttons())
    return STEP_ADMIN_SEARCH

async def admin_search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("ID має бути числом.", reply_markup=nav_buttons())
        return STEP_ADMIN_SEARCH

    uid = int(text)
    parts = [f"Історія клієнта {uid}:\n"]

    conn = sqlite3.connect(DB_NAME)
    deps = conn.execute("SELECT card, provider, payment, timestamp FROM deposits WHERE user_id=?", (uid,)).fetchall()
    parts.append("\nДепозити:")
    if deps:
        for r in deps:
            parts.append(f"{r[3]} — картка {r[0]}, {r[1]}, оплата {r[2]}")
    else:
        parts.append("— немає")

    wds = conn.execute("SELECT amount, method, details, timestamp FROM withdrawals WHERE user_id=?", (uid,)).fetchall()
    parts.append("\nВиведення:")
    if wds:
        for r in wds:
            parts.append(f"{r[3]} — {r[0]} via {r[1]}, реквізити {r[2]}")
    else:
        parts.append("— немає")

    await update.message.reply_text("\n".join(parts), reply_markup=nav_buttons())
    return STEP_MENU

# ————— Розсилка —————————————————————
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Введіть текст для розсилки:", reply_markup=nav_buttons())
    return STEP_ADMIN_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    conn = sqlite3.connect(DB_NAME)
    uids = [row[0] for row in conn.execute("SELECT DISTINCT user_id FROM clients WHERE authorized=1")]
    sent = 0
    for uid in uids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"Розсилка завершена. Відправлено {sent} повідомлень.", reply_markup=nav_buttons())
    return STEP_MENU

# ————— Reply адміну —————————————————————
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orig = update.message.reply_to_message
    if not orig:
        return
    admin_msg_id = orig.message_id

    row = sqlite3.connect(DB_NAME).execute(
        "SELECT user_id FROM threads WHERE admin_msg_id=?", (admin_msg_id,)
    ).fetchone()
    if not row:
        await update.message.reply_text("Ланцюг не знайдено.")
        return

    user_id = row[0]
    await context.bot.send_message(chat_id=user_id, text=update.message.text)
    await update.message.reply_text("✅ Доставлено.")
    return

def register_admin_handlers(app):
    # адмін-панель и базовые команды
    app.add_handler(CallbackQueryHandler(admin_panel,       pattern="^admin_panel$"), group=0)
    app.add_handler(CallbackQueryHandler(admin_deposits,    pattern="^admin_deposits$"), group=0)
    app.add_handler(CallbackQueryHandler(admin_users,       pattern="^admin_users$"), group=0)
    app.add_handler(CallbackQueryHandler(admin_withdrawals, pattern="^admin_withdrawals$"), group=0)
    app.add_handler(CallbackQueryHandler(admin_stats,       pattern="^admin_stats$"), group=0)
    app.add_handler(CallbackQueryHandler(admin_search_start,pattern="^admin_search$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_execute), group=1)
    app.add_handler(CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send), group=1)

    # reply-режим (ответ адмима пользователю)
    app.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_ID) & filters.REPLY & filters.TEXT
,
            admin_reply
        ),
        group=2
    )
