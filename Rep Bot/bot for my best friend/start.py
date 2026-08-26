import asyncio
import logging
import sys
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram import types

from config import TOKEN
from handlers import register_commands, register_callbacks
from handlers.message import check_rep_in_message

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def main():
    register_commands(dp, bot)
    register_callbacks(dp, bot)
    @dp.message()
    async def handle_all_messages(message: types.Message):
        await check_rep_in_message(message, bot)
    await dp.start_polling(bot)



if __name__ == "__main__":
    with sqlite3.connect("db.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id UNIQUE,
                username TEXT,
                join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                deposit INTEGER DEFAULT 0,
                is_banned BOOLEAN DEFAULT 0,
                ban_reason TEXT,
                rep_plus INTEGER DEFAULT 0,
                rep_minus INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reputation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                rating INTEGER CHECK(rating IN (1, -1)),
                message_id INTEGER,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                FOREIGN KEY (to_user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())