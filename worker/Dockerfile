FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY worker/src src/

# Команда запуска будет в docker-compose.yml
