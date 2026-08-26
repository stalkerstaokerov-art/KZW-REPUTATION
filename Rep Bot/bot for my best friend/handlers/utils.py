
from config import INFO_ID, NEWS_ID, REPS_ID
import sqlite3
from kb import rep_choice_kb

async def get_channel_name(bot, channel_id):
    try:
        chat = await bot.get_chat(channel_id)
        return chat.title
    except:
        return "Канал"

async def get_channel_link(bot, channel_id):
    try:
        chat = await bot.get_chat(channel_id)
        if chat.invite_link:
            return chat.invite_link
        elif chat.username:
            return f"https://t.me/{chat.username}"
        return None
    except:
        return None

async def is_subscribed(bot, user_id, channel_id):
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def check_subscriptions(bot, user_id):
    sub1 = await is_subscribed(bot, user_id, INFO_ID)
    sub2 = await is_subscribed(bot, user_id, NEWS_ID)
    sub3 = await is_subscribed(bot, user_id, REPS_ID)
    return sub1, sub2, sub3 

def generate_reputation_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=rs-{user_id}"


async def show_user_reputation(message, target_id: int):
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        result = cursor.execute("SELECT user_id, username, rep_plus, rep_minus, join_date FROM users WHERE user_id = ?", (target_id,)).fetchone()
        
        
        user_id_found, username_found, rep_plus, rep_minus, join_date = result
        await message.answer(f"<blockquote><b>Какую репутацию @{username_found} вы хотите посмотреть?</b></blockquote>",reply_markup=rep_choice_kb(user_id_found))
