from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# ----------------------------------------------------------------------
# Core Models
# ----------------------------------------------------------------------

class User(SQLModel, table=True):
    """
    Модель пользователя.
    user_id (tg) - первичный ключ, привязка всех данных.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True, unique=True)
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    tokens_limits: Optional[str] = None # Для будущих лимитов/токенов

    # Связь с чатами, которые принадлежат этому пользователю
    chats: List["Chat"] = Relationship(back_populates="owner")

    # Связь с сообщениями, которые принадлежат этому пользователю (через чаты)
    # messages: List["Message"] = Relationship(back_populates="owner") # Сложно, лучше через Chat

class Chat(SQLModel, table=True):
    """
    Модель чата.
    Ключевое требование: изоляция. Один и тот же chat_id может принадлежать
    разным пользователям (owner_id).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_chat_id: int = Field(index=True)
    owner_id: int = Field(foreign_key="user.telegram_user_id") # Владелец записи о чате
    title: Optional[str] = None
    is_parsing_enabled: bool = Field(default=False)
    
    # Связь с владельцем
    owner: User = Relationship(back_populates="chats")

    # Связь с сообщениями
    messages: List["Message"] = Relationship(back_populates="chat")

    # Уникальность по паре (telegram_chat_id, owner_id)
    __table_args__ = (
        Field(telegram_chat_id, index=True),
        Field(owner_id, index=True),
        {"unique_together": ("telegram_chat_id", "owner_id")}
    )

class Message(SQLModel, table=True):
    """
    Модель сообщения, которое было классифицировано как продажа.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_message_id: int
    chat_id: int = Field(foreign_key="chat.id") # Связь с записью чата в нашей БД
    author_telegram_user_id: int # ID автора сообщения в Telegram
    text: Optional[str] = None
    timestamp: datetime
    
    # Результаты классификации
    is_sale_message: bool = Field(default=False)
    nlp_check: bool = Field(default=False)
    llm_check: bool = Field(default=False)
    
    # Путь к медиа (локальное хранение)
    media_path: Optional[str] = None # Путь к папке /storage/{user_id}/{chat_id}/{message_id}/

    # Связь с чатом
    chat: Chat = Relationship(back_populates="messages")

    # Уникальность по паре (telegram_message_id, chat_id)
    __table_args__ = (
        Field(telegram_message_id, index=True),
        Field(chat_id, index=True),
        {"unique_together": ("telegram_message_id", "chat_id")}
    )

# ----------------------------------------------------------------------
# Database Setup
# ----------------------------------------------------------------------

# Файл с настройками БД будет создан отдельно (db.py)
