
from aiogram import types
from aiogram.filters import Command

from config import INFO_ID, NEWS_ID, REPS_ID, reload_admin_ids, ADMIN_IDS, ADMIN_ID
from handlers.utils import get_channel_name, check_subscriptions, get_channel_link, show_user_reputation, generate_reputation_link
from kb import main_kb, get_subscription_kb, rep_kb
from datetime import datetime
import sqlite3

def register_commands(dp, bot):
    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        args = message.text.split()  


        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            banned = cursor.execute("SELECT is_banned, ban_reason FROM users WHERE user_id = ?", (user_id,)).fetchone()
        
        if banned and banned[0] == 1:
            reason = banned[1] or "Не указана"
            await message.answer(
                f"🚫 <b>Вы заблокированы и не можете пользоваться функциями бота!</b>\n\n"
                f"📝 <b>Причина:</b> {reason}\n\n"
            )
            return
        
        if len(args) > 1 and args[1].startswith("rs-"):
            try:
                target_id = int(args[1].replace("rs-", ""))
                await show_user_reputation(message, target_id)
                return
            except:
                pass

        sub1, sub2, sub3 = await check_subscriptions(bot, user_id)

        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            exist = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()

            if not exist:
                cursor.execute("INSERT OR IGNORE INTO users(user_id,username,join_date) VALUES(?,?,?)", (user_id,username,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            conn.commit()

        if not sub1 or not sub2 or not sub3:
            name1 = await get_channel_name(bot, INFO_ID)
            name2 = await get_channel_name(bot, NEWS_ID)
            name3 = await get_channel_name(bot, REPS_ID)

            link1 = await get_channel_link(bot, INFO_ID)
            link2 = await get_channel_link(bot, NEWS_ID)
            link3 = await get_channel_link(bot, REPS_ID)
        
            keyboard = get_subscription_kb(link1, link2, link3, sub1, sub2, sub3, name1, name2, name3)
            await message.answer(f"<blockquote><b>🔒 Для использования бота необходимо подписаться на ресурсы ниже:</b></blockquote>",reply_markup=keyboard)
        else:
            await message.answer(f"<blockquote><b>🛡 KZW | РЕПУТАЦИЯ — система репутации\n\nПроверяй пользователей перед сделкой, оставляй репутацию и смотри за своей репутацией.</b></blockquote>", reply_markup=main_kb(user_id))

    @dp.message(Command("и"))
    async def get_user_info(message: types.Message):
        user_id = None
        args = message.text.split()

        if len(args) == 1 and not message.reply_to_message and not message.entities:
            return
        
        if message.chat.id != REPS_ID:
            return

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        
    
        elif message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    username = message.text[entity.offset:entity.offset + entity.length]
                    username = username.replace('@', '')
                
                    with sqlite3.connect("db.db") as conn:
                        cursor = conn.cursor()
                        result = cursor.execute("SELECT user_id, username, rep_plus, rep_minus, deposit, join_date FROM users WHERE username = ?", (username,)).fetchone()
                    
                    if result:
                        user_id = result[0]
                    else:
                        try:
                            member = await bot.get_chat_member(message.chat.id, username)
                            user_id = member.user.id
                        except:
                            user_id = None
                break
    
        if user_id:
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                result = cursor.execute("SELECT user_id, username, rep_plus, rep_minus, deposit, join_date, is_banned, ban_reason FROM users WHERE user_id = ?", (int(user_id),)).fetchone()

            if result:
                user_id_found, username_found, rep_plus, rep_minus, deposit, join_date, is_banned, ban_reason = result

            if user_id_found == message.from_user.id:
                if is_banned == 1:
                    return

            me = await bot.get_me()

            link = generate_reputation_link(me.username, user_id)


            total = rep_plus - rep_minus
            months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

            dt = datetime.strptime(join_date, "%Y-%m-%d %H:%M:%S")
            date_str = f"{dt.day} {months[dt.month-1]} {dt.year} года"
                
            total_votes = rep_plus + rep_minus
            if total_votes > 0:
                plus_percent = round((rep_plus / total_votes) * 100, 1)
                minus_percent = round((rep_minus / total_votes) * 100, 1)
            else:
                plus_percent = 0.0
                minus_percent = 0.0

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
            await message.reply(profile_text,reply_markup=rep_kb(link))
        else:
            await message.reply("<blockquote><b>❌ Пользователь не найден</b></blockquote>")

    @dp.message(Command("add"))
    async def add_admin_command(message: types.Message):
        """Добавить админа (только для текущих админов)"""
        if message.from_user.id not in ADMIN_ID:
            await message.answer("❌ У вас нет прав!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: /add <ID пользователя>")
            return
        
        try:
            new_admin_id = int(args[1])
        except:
            await message.answer("❌ Неверный формат! Введите число.")
            return
        
        # Проверяем, не админ ли уже
        if new_admin_id in ADMIN_IDS:
            await message.answer(f"❌ Пользователь {new_admin_id} уже админ!")
            return
        
        # Добавляем в .env
        with open("config_admins.env", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("ADMIN_IDS="):
                current_ids = line.strip().split("=")[1]
                if current_ids:
                    new_line = f"ADMIN_IDS={current_ids},{new_admin_id}\n"
                else:
                    new_line = f"ADMIN_IDS={new_admin_id}\n"
                lines[i] = new_line
                updated = True
                break
        
        if not updated:
            lines.append(f"ADMIN_IDS={new_admin_id}\n")
        
        with open("config_admins.env", "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        # Перезагружаем список админов
        reload_admin_ids()
        
        await message.answer(f"✅ Пользователь {new_admin_id} добавлен в админы!")

    @dp.message(Command("remove"))
    async def remove_admin_command(message: types.Message):
        """Удалить админа (только для текущих админов)"""
        if message.from_user.id not in ADMIN_ID:
            await message.answer("❌ У вас нет прав!")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: /remove <ID пользователя>")
            return
        
        try:
            remove_id = int(args[1])
        except:
            await message.answer("❌ Неверный формат! Введите число.")
            return
        
        # Нельзя удалить самого себя
        if remove_id == message.from_user.id:
            await message.answer("❌ Нельзя удалить самого себя!")
            return
        
        if remove_id not in ADMIN_IDS:
            await message.answer(f"❌ Пользователь {remove_id} не админ!")
            return
        
        # Удаляем из .env
        with open("config_admins.env", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.startswith("ADMIN_IDS="):
                current_ids = line.strip().split("=")[1]
                ids_list = [int(x.strip()) for x in current_ids.split(",") if x.strip()]
                ids_list = [x for x in ids_list if x != remove_id]
                new_line = f"ADMIN_IDS={','.join(str(x) for x in ids_list)}\n"
                lines[i] = new_line
                break
        
        with open("config_admins.env", "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        # Перезагружаем список админов
        reload_admin_ids()
        
        await message.answer(f"✅ Пользователь {remove_id} удален из админов!")
        



