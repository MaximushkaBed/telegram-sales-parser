from celery import Celery
from dotenv import load_dotenv
import os
from sqlmodel import Session, select
from .db import engine
from .models import Message, Chat
from .llm_classifier import classify_with_llm
from .nlp_classifier import classify_with_nlp
from .media_saver import save_media_files

load_dotenv()

# Настройка Celery
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task
def process_message(
    chat_id: int,
    message_id: int,
    author_id: int,
    text: str,
    timestamp: str,
    media_files: list
):
    """
    Основная задача по обработке и классификации сообщения.
    """
    print(f"Processing message {message_id} from chat {chat_id}...")
    
    with Session(engine) as session:
        # Находим запись чата в нашей БД
        chat_db = session.exec(select(Chat).where(Chat.telegram_chat_id == chat_id)).first()
        
        if not chat_db:
            print(f"Error: Chat with ID {chat_id} not found in DB.")
            return False

        # 1. Сохранение медиа
        # Получаем user_id владельца чата для изолированного хранения
        owner_user_id = chat_db.owner_id
        media_path = save_media_files(
            media_files=media_files,
            user_id=owner_user_id,
            chat_id=chat_id,
            message_id=message_id
        )
        
        # 2. Двойная классификация
        nlp_result = classify_with_nlp(text)
        llm_result = classify_with_llm(text)
        
        is_sale_message = nlp_result or llm_result
        
        # 3. Сохранение в БД
        message = Message(
            telegram_message_id=message_id,
            chat_id=chat_db.id,
            author_telegram_user_id=author_id,
            text=text,
            timestamp=timestamp,
            is_sale_message=is_sale_message,
            nlp_check=nlp_result,
            llm_check=llm_result,
            media_path=media_path
        )
        session.add(message)
        session.commit()
        print(f"Message {message_id} saved to DB. Sale: {is_sale_message}")

    return is_sale_message
