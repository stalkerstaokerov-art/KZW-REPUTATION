# handlers/message.py
import re
import sqlite3
from datetime import datetime, timedelta
from aiogram import types
from config import ADMIN_ID


async def check_rep_in_message(message: types.Message, bot):
    user_id = message.from_user.id
    text = message.text or message.caption or ""

    if message.chat.type not in ["group", "supergroup"]:
        return

    msg_id = message.message_id
    if not message.photo:
        return

    plus_match = re.search(r'\+rep', text, re.IGNORECASE)
    minus_match = re.search(r'\-rep', text, re.IGNORECASE)
    
    if not plus_match and not minus_match:
        return
    
    if plus_match:
        rating = 1
        rep_type = "+rep"
    else:
        rating = -1
        rep_type = "-rep"
    
    username_match = re.search(r'@(\w+)', text)
    
    if not username_match:
        return
    
    target_username = username_match.group(1)
    
    
    comment = text
    comment = re.sub(r'\+rep\s*', '', comment, flags=re.IGNORECASE)
    comment = re.sub(r'\-rep\s*', '', comment, flags=re.IGNORECASE)
    comment = re.sub(r'@\w+\s*', '', comment)
    comment = comment.strip()
    
    if not comment:
        return
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        target = cursor.execute("SELECT user_id, username FROM users WHERE username = ?", (target_username,)).fetchone()
        
        if not target:
            return
        
        target_id, target_name = target
    if user_id == target_id:
        await message.reply("❌ Вы не можете сами себе испортить или улучшить репутацию.")
        return
    
    if user_id not in ADMIN_ID:
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            last_review = cursor.execute("""SELECT created_at FROM reputation WHERE from_user_id = ? AND to_user_id = ? ORDER BY created_at DESC LIMIT 1""", (user_id, target_id)).fetchone()
            
            if last_review:
                last_time = datetime.strptime(last_review[0], "%Y-%m-%d %H:%M:%S")
                time_diff = datetime.now() - last_time
                
                if time_diff < timedelta(minutes=20):
                    remaining = 20 - (time_diff.seconds // 60)
                    await message.reply(
                        f"⏳ Вы уже ставили репутацию @{target_name}!\n"
                        f"Следующий раз можно будет через {remaining} минут."
                    )
                    return
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("""INSERT INTO reputation (from_user_id, to_user_id, rating, created_at, message_id, comment) VALUES (?, ?, ?, ?, ?, ?)""", (user_id, target_id, rating, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg_id,  comment))
        
        if rating == 1:
            cursor.execute("UPDATE users SET rep_plus = rep_plus + 1 WHERE user_id = ?", (target_id,))
        else:
            cursor.execute("UPDATE users SET rep_minus = rep_minus + 1 WHERE user_id = ?", (target_id,))
        
        conn.commit()
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        rep = cursor.execute("SELECT rep_plus, rep_minus FROM users WHERE user_id = ?", (target_id,)).fetchone()
        rep_plus, rep_minus = rep
        total_votes = rep_plus + rep_minus

        plus_percent = round((rep_plus / total_votes) * 100, 1) if total_votes > 0 else 0.0
        minus_percent = round((rep_minus / total_votes) * 100, 1) if total_votes > 0 else 0.0

    await message.reply(
        f"{rep_type} для @{target_name} ✅\n"
        f"📊 +Rep {plus_percent}% | -Rep {minus_percent}%\n"
        f"💬 {comment}"


    )
    
    await bot.send_message(target_id, f"📩 Вам оставили {rep_type}!\n💬 {comment}")