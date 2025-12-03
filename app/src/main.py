import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from .db import create_db_and_tables
from .handlers import router

load_dotenv()

# Инициализация aiogram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    """Основная функция для запуска бота в режиме Long Polling."""
    print("Starting bot in Long Polling mode...")
    
    # 1. Создание таблиц в БД
    create_db_and_tables()
    
    # 2. Удаление старого вебхука (если был)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Запуск Long Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")
