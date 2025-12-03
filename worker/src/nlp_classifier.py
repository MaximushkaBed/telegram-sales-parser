# Простая заглушка для NLP-классификатора
# В реальном проекте здесь будет spaCy/BERT-классификатор
# с поиском ключевых слов и проверкой структуры.

def classify_with_nlp(text: str) -> bool:
    """
    Простая NLP-классификация на основе ключевых слов.
    """
    if not text:
        return False
        
    text_lower = text.lower()
    
    keywords = ["продам", "продаю", "цена", "торг", "объявление", "куплю", "отдам"]
    
    for keyword in keywords:
        if keyword in text_lower:
            return True
            
    return False
