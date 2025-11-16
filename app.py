import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from handlers.user_private import user_private_router
from handlers.admin_private import admin_private_router
from dataBase.database import init_db
from scheduler import start_scheduler

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()

dp.include_routers(user_private_router, admin_private_router)

async def main():
    init_db()
    start_scheduler()
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
