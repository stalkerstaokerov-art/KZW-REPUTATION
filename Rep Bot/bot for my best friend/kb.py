from config import ADMIN_ID, ADMIN_IDS, reload_admin_ids
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_kb(user_id: int):
    reload_admin_ids()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile", style="primary"),
        InlineKeyboardButton(text="🔍 Поиск", callback_data="search", style="primary")
    ])

    if user_id in ADMIN_ID:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⚙️ Админ панель ⚙️", callback_data="admin_panel", style="danger")])

    if user_id in ADMIN_IDS:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🚫 Система банов", callback_data="admin_ban_system", style="danger")])
    
    return keyboard

def get_subscription_kb(channel_1_link, channel_2_link, channel_3_link, sub1, sub2, sub3, name1, name2, name3):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    if not sub1 and channel_1_link:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{name1}",
                url=channel_1_link,
                style="danger"
            )
        ])
    
    if not sub2 and channel_2_link:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{name2}",
                url=channel_2_link,
                style="danger"
            )
        ])

    if not sub3 and channel_3_link:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{name3}",
                url=channel_3_link,
                style="danger"
            )
        ])
    
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🔍 Проверить подписку",
            callback_data="check",
            style="success"
        )
    ])
    
    return keyboard



def back_kb():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu", style="primary")
    ])
    
    return keyboard


def rep_choice_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Все", callback_data=f"rep_show_{user_id}_all_0", style="primary")
        ],
        [
            InlineKeyboardButton(text="✅ Положительные", callback_data=f"rep_show_{user_id}_positive_0", style="success"),
            InlineKeyboardButton(text="❌ Отрицательные", callback_data=f"rep_show_{user_id}_negative_0", style="danger")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"menu", style="primary")
        ]
    ])


def reviews_kb(user_id: int, rep_type: str, current_page: int, total_pages: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    nav_buttons = []
    
    if current_page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅ Назад", callback_data=f"rep_show_{user_id}_{rep_type}_{current_page-1}", style="primary")
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅ Назад", callback_data="noop", style="primary")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data="noop", style="primary")
    )
    
    if current_page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ▶", callback_data=f"rep_show_{user_id}_{rep_type}_{current_page+1}", style="primary")
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ▶", callback_data="noop", style="primary")
        )
    
    keyboard.inline_keyboard.append(nav_buttons)
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu", style="primary")
    ])
    
    return keyboard


def profile_kb(user_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⭐️ Репутация", callback_data=f"rep_history_{user_id}", style="danger")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"menu", style="primary")
    ])
    return keyboard


def rep_kb(link: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⭐️ Репутация", url=link)
    ])
    return keyboard


def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
       # [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats", style="primary")],
        [InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_find_user", style="primary")],
        [InlineKeyboardButton(text="🚫 Система банов", callback_data="admin_ban_system", style="danger")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing", style="primary")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu", style="primary")]
    ])


def back_kb_second(call):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=call)
    ])
    return keyboard

def admin_ban_system_kb(user_id: int = None):
    reload_admin_ids()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user", style="primary")
    ])
    
    if user_id in ADMIN_IDS:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel", style="primary")
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="back", style="primary")
        ])
    return keyboard
    


def admin_user_manage_kb(user_id: int, is_banned: bool):
    if is_banned:
        ban_button = InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_unban_{user_id}", style="success")
    else:
        ban_button = InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_ban_{user_id}", style="danger")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([ban_button])
    
    if user_id not in ADMIN_IDS:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📊 Упр. репой", callback_data=f"admin_manage_rep_{user_id}", style="primary")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="💰 Пополнить депозит", callback_data=f"admin_add_deposit_{user_id}", style="success"),
            InlineKeyboardButton(text="💸 Вывести депозит", callback_data=f"admin_sub_deposit_{user_id}", style="danger")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад в админку", callback_data="admin_panel", style="primary")
        ])
    else:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="back", style="primary")
        ])
    
    return keyboard