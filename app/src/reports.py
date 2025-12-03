import pandas as pd
from sqlmodel import Session, select
from .db import engine
from .models import Message, Chat
from datetime import datetime
from typing import List

def generate_excel_report(user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bytes:
    """
    Генерирует Excel-отчет для пользователя.
    Возвращает байты файла Excel.
    """
    with Session(engine) as session:
        # 1. Находим все чаты, принадлежащие пользователю
        chat_statement = select(Chat).where(Chat.owner_id == user_id)
        user_chats: List[Chat] = session.exec(chat_statement).all()
        
        if not user_chats:
            raise ValueError("У пользователя нет активных чатов для отчета.")

        chat_ids = [chat.id for chat in user_chats]
        
        # 2. Формируем запрос на сообщения
        message_statement = select(Message).where(
            Message.chat_id.in_(chat_ids),
            Message.is_sale_message == True
        ).order_by(Message.timestamp.desc())
        
        if start_date:
            message_statement = message_statement.where(Message.timestamp >= start_date)
        if end_date:
            message_statement = message_statement.where(Message.timestamp <= end_date)
            
        messages: List[Message] = session.exec(message_statement).all()
        
        if not messages:
            raise ValueError("Не найдено сообщений о продаже за указанный период.")

        # 3. Подготовка данных для DataFrame
        data = []
        chat_titles = {chat.id: chat.title for chat in user_chats}
        
        for msg in messages:
            data.append({
                "Дата": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Чат": chat_titles.get(msg.chat_id, "Неизвестный чат"),
                "Текст сообщения": msg.text,
                "Автор (TG ID)": msg.author_telegram_user_id,
                "Продажа (NLP)": "Да" if msg.nlp_check else "Нет",
                "Продажа (LLM)": "Да" if msg.llm_check else "Нет",
                "Путь к медиа": msg.media_path if msg.media_path else "Нет"
            })
            
        df = pd.DataFrame(data)
        
        # 4. Генерация Excel-файла в памяти
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Сообщения о продаже', index=False)
        writer.close()
        output.seek(0)
        
        return output.getvalue()

import io
from typing import Optional
