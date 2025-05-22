            text = "\n\n".join([f"рџ‘¤ {r[0] or 'вЂ”'}\nРљР°СЂС‚РєР°: {r[1]}\nРџСЂРѕРІР°Р№РґРµСЂ: {r[2]}\nРћРїР»Р°С‚Р°: {r[3]}\nрџ•’ {r[4]}" for r in rows])
            await query.message.reply_text(f"РћСЃС‚Р°РЅРЅС– РїРѕРїРѕРІРЅРµРЅРЅСЏ:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_users":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, phone, status FROM registrations ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("РќРµРјР°С” Р·Р°СЂРµС”СЃС‚СЂРѕРІР°РЅРёС… РєРѕСЂРёСЃС‚СѓРІР°С‡С–РІ.")
        else:
            text = "\n\n".join([f"рџ‘¤ Р†РјвЂ™СЏ: {r[0]}\nрџ“ћ РўРµР»РµС„РѕРЅ: {r[1]}\nРЎС‚Р°С‚СѓСЃ: {r[2]}" for r in rows])
            await query.message.reply_text(f"РћСЃС‚Р°РЅРЅС– РєРѕСЂРёСЃС‚СѓРІР°С‡С–:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_withdrawals":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount TEXT,
                method TEXT,
                details TEXT,
                source_code TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("SELECT username, amount, method, details, source_code, timestamp FROM withdrawals ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("Р—Р°СЏРІРѕРє РЅР° РІРёРІРµРґРµРЅРЅСЏ РЅРµРјР°С”.")
        else:
            text = "\n\n".join([f"рџ‘¤ {r[0] or 'вЂ”'}\nрџ’ё РЎСѓРјР°: {r[1]}\nрџ’і РњРµС‚РѕРґ: {r[2]}\nрџ“Ґ Р РµРєРІС–Р·РёС‚Рё: {r[3]}\nрџ”ў РљРѕРґ: {r[4]}\nрџ•’ {r[5]}" for r in rows])
            await query.message.reply_text(f"РћСЃС‚Р°РЅРЅС– Р·Р°СЏРІРєРё РЅР° РІРёРІРµРґРµРЅРЅСЏ:\n\n{text}")
        return STEP_MENU

    if query.data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM registrations")
            users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM deposits")
            deposits = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM withdrawals")
            withdrawals = cur.fetchone()[0]
        text = f"рџ“Љ РЎС‚Р°С‚РёСЃС‚РёРєР°:\nрџ‘¤ РљРѕСЂРёСЃС‚СѓРІР°С‡С–РІ: {users}\nрџ’° РџРѕРїРѕРІРЅРµРЅСЊ: {deposits}\nрџ“„ Р’РёРІРµРґРµРЅСЊ: {withdrawals}"
        await query.message.reply_text(text)
        return STEP_MENU

    if query.data == "client":
        await query.message.reply_text("Р’РІРµРґС–С‚СЊ РЅРѕРјРµСЂ РєР°СЂС‚РєРё РєР»С–С”РЅС‚Р° РєР»СѓР±Сѓ:", reply_markup=nav_buttons())
        return STEP_CLIENT_CARD

    if query.data in ("back", "home"):
        return await start(update, context)

    await query.message.reply_text("Р¦СЏ С„СѓРЅРєС†С–СЏ С‰Рµ РІ СЂРѕР·СЂРѕР±С†С–.", reply_markup=nav_buttons())
    return STEP_MENU