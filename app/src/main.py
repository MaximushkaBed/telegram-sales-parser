import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from .db import create_db_and_tables
from .handlers import router

load_dotenv()

# Инициализация FastAPI
app = FastAPI(title="Telegram Sales Parser Bot API")

# Инициализация aiogram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL") # Должен быть публичным URL
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

@app.on_event("startup")
async def on_startup():
    """Действия при запуске приложения."""
    # 1. Создание таблиц в БД
    create_db_and_tables()
    
    # 2. Установка вебхука
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != f"{WEBHOOK_URL}{WEBHOOK_PATH}":
        await bot.set_webhook(url=f"{WEBHOOK_URL}{WEBHOOK_PATH}")
        print(f"Webhook set to: {WEBHOOK_URL}{WEBHOOK_PATH}")
    else:
        print(f"Webhook is already set to: {WEBHOOK_URL}{WEBHOOK_PATH}")

@app.on_event("shutdown")
async def on_shutdown():
    """Действия при остановке приложения."""
    # 1. Удаление вебхука
    await bot.delete_webhook()
    print("Webhook deleted.")

@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    """Обработка входящих обновлений от Telegram."""
    try:
        # Получаем тело запроса
        update_json = await request.json()
        update = Update.model_validate(update_json, context={"bot": bot})
        
        # Обрабатываем обновление через диспетчер aiogram
        await dp.feed_update(bot=bot, update=update)
        
        return {"ok": True}
    except Exception as e:
        print(f"Error processing update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "message": "Bot API is running"}
