import os
import requests
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_STORAGE_PATH = "/app/storage" # Путь внутри контейнера

def save_media_files(
    media_files: List[dict],
    user_id: int,
    chat_id: int,
    message_id: int
) -> Optional[str]:
    """
    Скачивает медиафайлы из Telegram и сохраняет их в изолированную папку.
    Возвращает путь к папке с медиафайлами.
    """
    if not media_files:
        return None

    # Формирование изолированного пути
    # /storage/{user_id}/{chat_id}/{message_id}/
    relative_path = f"{user_id}/{chat_id}/{message_id}"
    full_path = os.path.join(BASE_STORAGE_PATH, relative_path)
    
    os.makedirs(full_path, exist_ok=True)
    
    for i, media_info in enumerate(media_files):
        file_id = media_info.get("file_id")
        file_extension = media_info.get("file_extension", ".bin")
        
        if not file_id:
            continue

        try:
            # 1. Получение информации о файле (file_path)
            file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            response = requests.get(file_info_url)
            response.raise_for_status()
            file_path = response.json()["result"]["file_path"]
            
            # 2. Скачивание файла
            download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            file_response = requests.get(download_url, stream=True)
            file_response.raise_for_status()
            
            # 3. Сохранение на диск
            file_name = f"media_{i+1}{file_extension}"
            save_path = os.path.join(full_path, file_name)
            
            with open(save_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Saved file {file_name} to {save_path}")

        except Exception as e:
            print(f"Error saving media file {file_id}: {e}")
            # Продолжаем, даже если один файл не удалось сохранить
            continue
            
    return relative_path
