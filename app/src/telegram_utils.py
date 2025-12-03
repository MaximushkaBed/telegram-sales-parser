from aiogram import Bot
from aiogram.types import ChatMember
from typing import Optional

async def get_chat_member_status(bot: Bot, chat_id: int, user_id: int) -> Optional[str]:
    """Получает статус пользователя в чате."""
    try:
        member: ChatMember = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status
    except Exception as e:
        # Например, если бот не состоит в чате или чат не существует
        print(f"Error getting chat member status for chat {chat_id} and user {user_id}: {e}")
        return None

async def is_bot_admin(bot: Bot, chat_id: int) -> bool:
    """Проверяет, является ли бот администратором в чате."""
    try:
        me: ChatMember = await bot.get_chat_member(chat_id=chat_id, user_id=bot.id)
        return me.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Error checking bot admin status in chat {chat_id}: {e}")
        return False

async def get_chat_title(bot: Bot, chat_id: int) -> Optional[str]:
    """Получает название чата."""
    try:
        chat = await bot.get_chat(chat_id=chat_id)
        return chat.title
    except Exception as e:
        print(f"Error getting chat title for chat {chat_id}: {e}")
        return None
