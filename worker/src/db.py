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

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Используем синхронный движок для Celery
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    """Возвращает синхронную сессию для Celery."""
    from sqlmodel import Session
    with Session(engine) as session:
        yield session
