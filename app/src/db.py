from sqlmodel import create_engine, SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

# Параметры подключения из .env
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Создает таблицы в базе данных на основе моделей SQLModel."""
    # Импортируем модели, чтобы они были известны SQLModel
    from .models import User, Chat, Message
    
    SQLModel.metadata.create_all(engine)

# Асинхронный движок для FastAPI/aiogram
# from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine
# async_engine = AsyncEngine(create_engine(DATABASE_URL, echo=True, future=True))

# async def get_session() -> AsyncSession:
#     async with AsyncSession(async_engine) as session:
#         yield session
