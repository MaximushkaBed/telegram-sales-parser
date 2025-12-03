from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Инициализация клиента OpenAI
# Предполагается, что OPENAI_API_KEY установлен в .env
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url может быть изменен для других провайдеров (Groq, Mistral, Local)
)

def classify_with_llm(text: str) -> bool:
    """
    Внешняя LLM-проверка: "Это сообщение является объявлением о продаже? Ответ: Да/Нет."
    """
    if not text:
        return False

    prompt = (
        "Проанализируй следующее сообщение. Является ли оно объявлением о продаже, "
        "покупке или обмене товаров/услуг? Ответь только 'Да' или 'Нет'."
        f"\n\nСообщение: \"{text}\""
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": "Ты — высокоточный классификатор сообщений. Отвечай только 'Да' или 'Нет'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        
        llm_response = response.choices[0].message.content.strip().lower()
        
        return llm_response == "да"

    except Exception as e:
        print(f"Error during LLM classification: {e}")
        # В случае ошибки LLM считаем, что это не продажа, чтобы избежать ложных срабатываний
        return False
