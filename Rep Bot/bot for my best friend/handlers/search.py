# handlers/search.py
import sqlite3
from datetime import datetime
from aiogram import types
from aiogram.fsm.context import FSMContext

from handlers.states import SearchStates
from kb import back_kb, profile_kb
from handlers.utils import generate_reputation_link


async def process_search_input(message: types.Message, state: FSMContext):
    text = message.text.strip()
    
    if not text:
        await message.answer("❌ Введите текст для поиска")
        await state.clear()
        return
    
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        

        if text.isdigit():
            result = cursor.execute("SELECT user_id, username, rep_plus, rep_minus, deposit, join_date, is_banned, ban_reason FROM users WHERE user_id = ?", (int(text),)).fetchone()
    
        elif text.startswith("@"):
            username = text[1:]
            result = cursor.execute("SELECT user_id, username, rep_plus, rep_minus, deposit, join_date, is_banned, ban_reason FROM users WHERE username = ?", (username,)).fetchone()
        
        if result:
            user_id_found, username_found, rep_plus, rep_minus, deposit, join_date, is_banned, ban_reason = result
            total = rep_plus - rep_minus

            dt = datetime.strptime(join_date, "%Y-%m-%d %H:%M:%S")
            months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
            date_str = f"{dt.day} {months[dt.month-1]} {dt.year} года"

            total_votes = rep_plus + rep_minus
            if total_votes > 0:
                plus_percent = round((rep_plus / total_votes) * 100, 1)
                minus_percent = round((rep_minus / total_votes) * 100, 1)
            else:
                plus_percent = 0.0
                minus_percent = 0.0

            me = await message.bot.get_me()

            link = generate_reputation_link(me.username, user_id_found)

            if is_banned == 1:
                text = f"🛑 ЗАБЛОКИРОВАН: {ban_reason}\n\n"
            else: 
                text = ""

            profile_text = (
                f"{text}"
                f"<b>🤵‍♂️ @{username_found} [ <code>{user_id_found}</code> ]</b>\n\n"
                f"<blockquote>⭐️ <b><a href='{link}'>Репутация</a></b> {total} REP\n"
                f"➕ {plus_percent}%\n"
                f"➖ {minus_percent}%</blockquote>\n"
                f"<blockquote>🏦 <b>Депозит</b> {deposit}$</blockquote>\n"
                f"<blockquote>❗ <b>ВНИМАНИЕ СМОТРИТЕ ПОЛЕ «О СЕБЕ»</b></blockquote>\n\n"
                f"📅 <b>В системе с {date_str}</b>"
            )
            await message.answer(profile_text,reply_markup=profile_kb(user_id_found))
        else:
            await message.reply("<blockquote><b>❌ Пользователь не найден</b></blockquote>",reply_markup=back_kb())
    
    await state.clear()