import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from db.database import init_db
from handlers.middlewares import AuthMiddleware
from handlers.bot_handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Создание таблиц в Neon.tech
    logging.info("Инициализация базы данных...")
    init_db()

    # 2. Инициализация бота
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # 3. Middleware авторизации (только для вашего User ID)
    dp.message.outer_middleware(AuthMiddleware())

    # 4. Регистрация роутеров
    dp.include_router(router)

    logging.info("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())