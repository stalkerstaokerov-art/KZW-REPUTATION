from config import INFO_ID, NEWS_ID, REPS_ID, ADMIN_ID, ADMIN_IDS, reload_admin_ids
from handlers.utils import check_subscriptions, get_channel_name, get_channel_link, generate_reputation_link
from kb import get_subscription_kb, profile_kb, main_kb, back_kb, rep_choice_kb, admin_panel_kb, back_kb_second, admin_ban_system_kb, admin_user_manage_kb
import sqlite3
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram import types
from handlers.states import SearchStates
from handlers.search import process_search_input
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def register_callbacks(dp, bot):
    def is_admin(user_id: int) -> bool:
        """Главный админ (полный доступ)"""
        return user_id in ADMIN_ID
    
    def is_ban_admin(user_id: int) -> bool:
        """Обычный админ (только бан)"""
        return user_id in ADMIN_IDS
    # ====================================

    def check_subscription_required(handler):
        async def wrapper(callback, state=None):
            user_id = callback.from_user.id
            sub1, sub2, sub3 = await check_subscriptions(bot, user_id)
            if not sub1 or not sub2 or not sub3:
                await callback.answer("Сначала выполни все требования", show_alert=True)
                return
            
            return await handler(callback, state)
        return wrapper

    @dp.callback_query(lambda c: c.data == "check")
    async def check_callback(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        
        sub1, sub2, sub3 = await check_subscriptions(bot, user_id)
        
        if sub1 and sub2 and sub3:
            await callback.message.edit_text("<blockquote><b>✅ Всё готово! Теперь вы можете пользоваться ботом!</b></blockquote>")
        else:
            name1 = await get_channel_name(bot, INFO_ID)
            name2 = await get_channel_name(bot, NEWS_ID)
            name3 = await get_channel_name(bot, REPS_ID)
            
            msg = "Еще не выполнено:\n"
            if not sub1:
                msg += f"• {name1}\n"
            if not sub2:
                msg += f"• {name2}\n"
            if not sub3:
                msg += f"• {name3}\n"

            await callback.answer(msg, show_alert=True)

    @dp.callback_query(lambda c: c.data == "profile")
    @check_subscription_required
    async def profile_callback(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()

        user_id = callback.from_user.id
        username = callback.from_user.username or callback.from_user.first_name
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            rep_plus = cursor.execute("SELECT rep_plus FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
            rep_minus = cursor.execute("SELECT rep_minus FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
            deposit = cursor.execute("SELECT deposit FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
            join_date = cursor.execute("SELECT join_date FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
            
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
            
            me = await bot.get_me()
            link = generate_reputation_link(me.username, user_id)
            
            profile_text = (
                f"<b>🤵‍♂️ @{username} [ <code>{user_id}</code> ]</b>\n\n"
                f"<blockquote>⭐️ <b><a href='{link}'>Репутация</a></b> {total} REP\n"
                f"➕ {plus_percent}%\n"
                f"➖ {minus_percent}%</blockquote>\n"
                f"<blockquote>🏦 <b>Депозит</b> {deposit}$</blockquote>\n"
                f"<blockquote>❗ <b>ВНИМАНИЕ СМОТРИТЕ ПОЛЕ «О СЕБЕ»</b></blockquote>\n\n"
                f"📅 <b>В системе с {date_str}</b>"
            )
            
            await callback.message.edit_text(profile_text, reply_markup=profile_kb(user_id))
            await callback.answer()

    @dp.callback_query(lambda c: c.data == "search")
    @check_subscription_required
    async def search_callback(callback: types.CallbackQuery, state: FSMContext):
        await state.set_state(SearchStates.waiting_for_search)
        msg = await callback.message.edit_text(
            "<blockquote><b>🔍 Введите @юзернейм или ID пользователя для поиска.</b></blockquote>",
            reply_markup=back_kb()
        )
        await state.update_data(msg_id=msg.message_id)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "menu")
    async def menu_callback(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        await callback.message.edit_text(
            "<blockquote><b>🛡 KZW | РЕПУТАЦИЯ — система репутации\n\nПроверяй пользователей перед сделкой, оставляй репутацию и смотри за своей репутацией.</b></blockquote>",
            reply_markup=main_kb(user_id)
        )

    @dp.message(SearchStates.waiting_for_search)
    async def handle_search_input(message: types.Message, state: FSMContext):
        data = await state.get_data()
        msg_id = data.get('msg_id')
        await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        await process_search_input(message, state)

    @dp.callback_query(lambda c: c.data == "menu_pel")
    async def menu_pel_callback(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        await callback.message.edit_text(
            "<blockquote><b>🛡 KZW | РЕПУТАЦИЯ — система репутации\n\nПроверяй пользователей перед сделкой, оставляй репутацию и смотри за своей репутацией.</b></blockquote>",
            reply_markup=main_kb(user_id)
        )

    @dp.callback_query(lambda c: c.data.startswith("rep_history_"))
    @check_subscription_required
    async def rep_history_callback(callback: types.CallbackQuery, state: FSMContext):
        user_id = int(callback.data.split("_")[2])
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,)).fetchone()
            username = user[0] if user else "Пользователь"
        
        await callback.message.edit_text(
            f"<blockquote><b>Какую репутацию @{username} вы хотите посмотреть?</b></blockquote>",
            reply_markup=rep_choice_kb(user_id)
        )
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("rep_show_"))
    @check_subscription_required
    async def show_reviews(callback: types.CallbackQuery, state: FSMContext):
        data = callback.data.split("_")
        target_user_id = int(data[2])
        rep_type = data[3]
        page = int(data[4]) if len(data) > 4 else 0
        per_page = 5
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (target_user_id,)).fetchone()
            username = user[0] if user else "Пользователь"
            
            if rep_type == "positive":
                total = cursor.execute("SELECT COUNT(*) FROM reputation WHERE to_user_id = ? AND rating = 1", (target_user_id,)).fetchone()[0]
            elif rep_type == "negative":
                total = cursor.execute("SELECT COUNT(*) FROM reputation WHERE to_user_id = ? AND rating = -1", (target_user_id,)).fetchone()[0]
            else:
                total = cursor.execute("SELECT COUNT(*) FROM reputation WHERE to_user_id = ?", (target_user_id,)).fetchone()[0]
            
            if rep_type == "positive":
                reviews = cursor.execute(
                    "SELECT id, from_user_id, rating, created_at FROM reputation WHERE to_user_id = ? AND rating = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (target_user_id, per_page, page * per_page)
                ).fetchall()
            elif rep_type == "negative":
                reviews = cursor.execute(
                    "SELECT id, from_user_id, rating, created_at FROM reputation WHERE to_user_id = ? AND rating = -1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (target_user_id, per_page, page * per_page)
                ).fetchall()
            else:
                reviews = cursor.execute(
                    "SELECT id, from_user_id, rating, created_at FROM reputation WHERE to_user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (target_user_id, per_page, page * per_page)
                ).fetchall()
        
        if total == 0:
            await callback.answer("Отзывов не найдено", show_alert=True)
            return
        
        type_names = {"all": "Все", "positive": "Положительные", "negative": "Отрицательные"}
        title = f"Отзывы для @{username} — {type_names[rep_type]} ({total})"
        if rep_type == "positive":
            title += " 🎉"
        elif rep_type == "negative":
            title += " 😔"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for review_id, from_id, rating, created_at in reviews:
            with sqlite3.connect("db.db") as conn:
                cursor = conn.cursor()
                from_user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (from_id,)).fetchone()
                from_name = from_user[0] if from_user else str(from_id)
            
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d.%m.%y")
            except:
                date_str = "неизвестно"
            
            sign = "+rep" if rating == 1 else "-rep"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{sign} от @{from_name} · {date_str}",
                    callback_data=f"review_detail_{review_id}",
                    style="primary" if rating == 1 else "danger"
                )
            ])
        
        keyboard.inline_keyboard.append([])
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅ Назад", callback_data=f"rep_show_{target_user_id}_{rep_type}_{page-1}", style="primary")
            )
        else:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅ Назад", callback_data="noop", style="primary")
            )
        
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="Вперёд ▶", callback_data=f"rep_show_{target_user_id}_{rep_type}_{page+1}", style="primary")
            )
        else:
            nav_buttons.append(
                InlineKeyboardButton(text="Вперёд ▶", callback_data="noop", style="primary")
            )
        
        keyboard.inline_keyboard.append(nav_buttons)
        keyboard.inline_keyboard.append([])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"rep_history_{target_user_id}", style="primary")
        ])
        
        await callback.message.edit_text(
            f"<b><blockquote>{title}</blockquote></b>",
            reply_markup=keyboard
        )
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "noop")
    async def noop_callback(callback: types.CallbackQuery):
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("review_detail_"))
    @check_subscription_required
    async def review_detail_callback(callback: types.CallbackQuery, state: FSMContext):
        review_id = int(callback.data.split("_")[2])
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            review = cursor.execute("SELECT from_user_id, to_user_id, rating, created_at, comment, message_id FROM reputation WHERE id = ?",(review_id,)).fetchone()
            
            if not review:
                await callback.answer("❌ Отзыв не найден", show_alert=True)
                return
            
            from_id, to_id, rating, created_at, comment, msg_id = review

            from_user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (from_id,)).fetchone()
            to_user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (to_id,)).fetchone()
            
            from_name = from_user[0] if from_user else str(from_id)
            to_name = to_user[0] if to_user else str(to_id)
            
            months = {
                'January': 'января', 'February': 'февраля', 'March': 'марта',
                'April': 'апреля', 'May': 'мая', 'June': 'июня',
                'July': 'июля', 'August': 'августа', 'September': 'сентября',
                'October': 'октября', 'November': 'ноября', 'December': 'декабря'
            }
            
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                date_str = f"{dt.day} {months[dt.strftime('%B')]} {dt.year} года"
            except:
                date_str = "неизвестно"
            
            sign = "✅ Положительный" if rating == 1 else "➖ Отрицательный"
            me = await bot.get_me()

            link_sender = generate_reputation_link(me.username, from_id)
            link_to = generate_reputation_link(me.username, to_id)
            
            text = f"""
<blockquote><b>{sign} отзыв

👤 Отправитель: <a href='{link_sender}'>@{from_name}</a>
👤 Получатель: <a href='{link_to}'>@{to_name}</a>
📅 Дата: {date_str}</b></blockquote>

💬 Комментарий
{comment}
"""     
        if msg_id:
            await bot.forward_message(chat_id=callback.from_user.id, from_chat_id=REPS_ID, message_id=msg_id)
        await callback.message.answer(text)

    @dp.callback_query(lambda c: c.data == "back")
    async def back_callback(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        await callback.message.edit_text("<blockquote><b>🛡 KZW | РЕПУТАЦИЯ — система репутации\n\nПроверяй пользователей перед сделкой, оставляй репутацию и смотри за своей репутацией.</b></blockquote>",reply_markup=main_kb(user_id))
        await callback.answer()

    
    @dp.callback_query(lambda c: c.data == "admin_panel")
    async def admin_callback(callback: types.CallbackQuery, state: FSMContext):
        print(is_admin(callback.from_user.id))
        if is_admin(callback.from_user.id) != True:
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        await callback.message.edit_text("<blockquote><b>Админ-Панель</b></blockquote>", reply_markup=admin_panel_kb())
        await callback.answer()

    @dp.callback_query(lambda c: c.data == 'admin_mailing')
    async def mailing_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        await state.set_state(SearchStates.waiting_for_mailing)
        msg = await callback.message.edit_text("📢 Введите текст для рассылки:", reply_markup=back_kb_second("admin_panel"))
        await state.update_data(msg_id=msg.message_id)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "admin_ban_system")
    async def admin_ban_system_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id) and not is_ban_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            banned_count = cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]
        
        await callback.message.edit_text(
            f"<b>🚫 Система банов</b>\n\n"
            f"👥 Забаненных пользователей: {banned_count}\n\n"
            f"Выбери действие:",
            reply_markup=admin_ban_system_kb()
        )
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "admin_find_user")
    async def admin_find_user_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id) and not is_ban_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        await state.set_state(SearchStates.waiting_for_admin_search)
        msg = await callback.message.edit_text("🔍 Введите @юзернейм или ID пользователя для поиска:", reply_markup=back_kb_second("admin_panel"))
        await state.update_data(msg_id=msg.message_id)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("admin_ban_"))
    async def admin_ban_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id) and not is_ban_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return

        target_id = int(callback.data.split("_")[2])
    
        await state.set_state(SearchStates.waiting_for_ban_reason)
        await state.update_data(target_id=target_id)
        if is_admin(callback.from_user.id):
            await callback.message.edit_text("🚫 Введите причину бана:",reply_markup=back_kb_second("admin_panel"))
        else:
            await callback.message.edit_text("🚫 Введите причину бана:",reply_markup=back_kb_second("back"))
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("admin_unban_"))
    async def admin_unban_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id) and not is_ban_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        target_id = int(callback.data.split("_")[2])
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
            conn.commit()
            user = cursor.execute("SELECT username, is_banned FROM users WHERE user_id = ?", (target_id,)).fetchone()
        
        await callback.answer("✅ Пользователь разбанен!", show_alert=True)

        try:
            await bot.unban_chat_member(chat_id=REPS_ID,user_id=target_id)
            await bot.send_message(target_id, "✅ Вы были разбанены!")
        except:
            pass
    @dp.callback_query(lambda c: c.data.startswith("admin_add_deposit_"))
    async def admin_add_deposit_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        target_id = int(callback.data.split("_")[3])
        await state.set_state(SearchStates.waiting_for_deposit_amount)
        await state.update_data(target_id=target_id, action="add")
        
        await callback.message.edit_text("💰 Введите сумму для пополнения депозита:", reply_markup=back_kb_second("admin_panel"))
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("admin_sub_deposit_"))
    async def admin_sub_deposit_callback(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        target_id = int(callback.data.split("_")[3])
        await state.set_state(SearchStates.waiting_for_deposit_amount)
        await state.update_data(target_id=target_id, action="sub")
        
        await callback.message.edit_text("💸 Введите сумму для вывода с депозита:", reply_markup=back_kb_second("admin_panel"))
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("admin_manage_rep_"))
    async def admin_manage_rep_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        target_id = int(callback.data.split("_")[3])
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            user = cursor.execute("SELECT username, rep_plus, rep_minus FROM users WHERE user_id = ?", (target_id,)).fetchone()
            username = user[0] if user else "Пользователь"
            rep_plus = user[1] if user else 0
            rep_minus = user[2] if user else 0
            total = rep_plus - rep_minus
            
            reviews = cursor.execute("""
                SELECT id, from_user_id, rating, created_at, comment 
                FROM reputation 
                WHERE to_user_id = ? 
                ORDER BY created_at DESC
            """, (target_id,)).fetchall()
        
        text = f"""
<b>📊 Управление репутацией</b>

👤 @{username}
📊 Репутация: {total} (+{rep_plus}/-{rep_minus})
📝 Всего отзывов: {len(reviews)}

Выберите отзыв для удаления:
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        if reviews:
            for review_id, from_id, rating, created_at, comment in reviews[:10]:
                with sqlite3.connect("db.db") as conn:
                    cursor = conn.cursor()
                    from_user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (from_id,)).fetchone()
                    from_name = from_user[0] if from_user else str(from_id)
                
                sign = "➕" if rating == 1 else "➖"
                try:
                    dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d.%m.%y")
                except:
                    date_str = "неизвестно"
                
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"{sign} {from_name} · {date_str}",
                        callback_data=f"admin_delete_review_{review_id}_{target_id}",
                        style="danger"
                    )
                ])
        else:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="📋 Нет отзывов", callback_data="noop", style="primary")
            ])
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_panel", style="primary")
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("admin_delete_review_"))
    async def admin_delete_review_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав!", show_alert=True)
            return
        
        data = callback.data.split("_")
        review_id = int(data[3])
        target_id = int(data[4])
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            
            review = cursor.execute("SELECT rating, to_user_id FROM reputation WHERE id = ?", (review_id,)).fetchone()
            
            if not review:
                await callback.answer("❌ Отзыв не найден", show_alert=True)
                return
            
            rating, to_user_id = review
            
            cursor.execute("DELETE FROM reputation WHERE id = ?", (review_id,))
            
            if rating == 1:
                cursor.execute("UPDATE users SET rep_plus = rep_plus - 1 WHERE user_id = ?", (to_user_id,))
            else:
                cursor.execute("UPDATE users SET rep_minus = rep_minus - 1 WHERE user_id = ?", (to_user_id,))
            
            conn.commit()
        
        await callback.answer("🗑 Отзыв удален!", show_alert=True)
        
        await admin_manage_rep_callback(callback)

    @dp.message(SearchStates.waiting_for_deposit_amount)
    async def deposit_amount_input(message: types.Message, state: FSMContext):
        data = await state.get_data()
        target_id = data.get('target_id')
        action = data.get('action')
        
        if not target_id or action not in ["add", "sub"]:
            return
        
        try:
            amount = int(message.text)
            if amount <= 0:
                await message.answer("❌ Сумма должна быть больше 0!")
                return
        except:
            await message.answer("❌ Введите число!")
            return
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            
            if action == "add":
                cursor.execute("UPDATE users SET deposit = deposit + ? WHERE user_id = ?", (amount, target_id))
                action_text = f"💰 Пополнено на {amount}$"
            else:
                current = cursor.execute("SELECT deposit FROM users WHERE user_id = ?", (target_id,)).fetchone()[0]
                if current < amount:
                    await message.answer(f"❌ На депозите всего {current}$, нельзя вывести {amount}$!")
                    return
                cursor.execute("UPDATE users SET deposit = deposit - ? WHERE user_id = ?", (amount, target_id))
                action_text = f"💸 Выведено {amount}$"
            
            conn.commit()
            user = cursor.execute("SELECT username, deposit FROM users WHERE user_id = ?", (target_id,)).fetchone()
        
        await message.answer(
            f"✅ {action_text} пользователю @{user[0]}!\n\n"
            f"💰 Теперь депозит: {user[1]}$",
            reply_markup=admin_user_manage_kb(target_id, False)
        )
        await state.clear()

    @dp.message(SearchStates.waiting_for_ban_reason)
    async def admin_ban_reason_input(message: types.Message, state: FSMContext):
        data = await state.get_data()
        target_id = data.get('target_id')
    
        if not target_id:
            await message.answer("❌ Ошибка! Попробуйте снова.", reply_markup=back_kb_second("admin_panel"))
            await state.clear()
            return
    
        reason = message.text.strip()
        if not reason:
            await message.answer("❌ Причина не может быть пустой!")
            return
    
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", (reason, target_id))
            conn.commit()
            user = cursor.execute("SELECT username FROM users WHERE user_id = ?", (target_id,)).fetchone()
    
        await message.answer(
            f"🚫 <b>Пользователь @{user[0]} забанен!</b>\n\n"
            f"📝 <b>Причина:</b> {reason}"
        )

        try:
            await bot.ban_chat_member(chat_id=REPS_ID,user_id=target_id)
            await bot.send_message(target_id,
                f"🚫 <b>Вы были забанены!</b>\n\n"
                f"📝 <b>Причина:</b> {reason}\n\n"
            )
        except:
            pass
    
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            await message.answer("<blockquote><b>Админ-Панель</b></blockquote>", reply_markup=admin_panel_kb())
        else:
            await message.answer("<blockquote><b>🛡 KZW | РЕПУТАЦИЯ — система репутации\n\nПроверяй пользователей перед сделкой, оставляй репутацию и смотри за своей репутацией.</b></blockquote>", reply_markup=main_kb(user_id))
    

        await state.clear()

    @dp.message(SearchStates.waiting_for_admin_search)
    async def admin_search_input(message: types.Message, state: FSMContext):
        data = await state.get_data()
        msg_id = data.get('msg_id')
        await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        await message.delete()
        
        text = message.text.strip()
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            
            if text.isdigit():
                result = cursor.execute("SELECT user_id, username, deposit, is_banned, rep_plus, rep_minus FROM users WHERE user_id = ?",(int(text),)).fetchone()
            elif text.startswith("@"):
                username = text[1:]
                result = cursor.execute("SELECT user_id, username, deposit, is_banned, rep_plus, rep_minus FROM users WHERE username = ?",(username,)).fetchone()
            else:
                result = cursor.execute("SELECT user_id, username, deposit, is_banned, rep_plus, rep_minus FROM users WHERE username LIKE ?",(f"%{text}%",)).fetchone()
            
            if not result:
                await message.answer("❌ Пользователь не найден", reply_markup=back_kb_second("admin_panel"))
                await state.clear()
                return
            
            user_id_found, username_found, deposit, is_banned, rep_plus, rep_minus = result
            total = rep_plus - rep_minus
            status = "🔒 Забанен" if is_banned else "✅ Активен"
            
            await message.answer(
                f"<b>👤 Найден пользователь</b>\n\n"
                f"🆔 ID: <code>{user_id_found}</code>\n"
                f"👤 Username: @{username_found or 'Не указан'}\n"
                f"📊 Репутация: {total} (+{rep_plus}/-{rep_minus})\n"
                f"💰 Депозит: {deposit}$\n"
                f"🚫 Статус: {status}",
                reply_markup=admin_user_manage_kb(user_id_found, is_banned),
                parse_mode="HTML"
            )
        
        await state.clear()
    
    @dp.message(SearchStates.waiting_for_mailing)
    async def admin_mailing_send(message: types.Message, state: FSMContext):
        data = await state.get_data()
        msg_id = data.get('msg_id')
        await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        await message.delete()

        text = message.text
        
        with sqlite3.connect("db.db") as conn:
            cursor = conn.cursor()
            users = cursor.execute("SELECT user_id FROM users WHERE is_banned = 0").fetchall()
        
        
        success = 0
        fail = 0
        
        for user in users:
            try:
                await bot.send_message(user[0],text)
                success += 1
            except:
                fail += 1

        await bot.send_message(REPS_ID,text)
        
        await message.answer(
            f"✅ Рассылка отправлена!\n\n"
            f"📨 Доставлено: {success}\n"
            f"❌ Не доставлено: {fail}",
            reply_markup=back_kb_second("admin_panel")
        )
        await state.clear()