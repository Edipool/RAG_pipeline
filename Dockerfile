# Общий базовый образ для обоих сервисов
FROM python:3.10-slim AS base

# Устанавливаем рабочую директорию
WORKDIR /project

# Копируем только файлы зависимостей для Poetry
COPY pyproject.toml poetry.lock ./

# Устанавливаем Poetry и зависимости
RUN pip install --no-cache-dir poetry && poetry install --no-root

# Копируем все файлы проекта
COPY . .

# Сборка для бэкенда
FROM base AS backend

# Устанавливаем рабочую директорию для бэкенда
WORKDIR /project/backend

# Добавляем корневую директорию в PYTHONPATH
ENV PYTHONPATH="/project"

# Открываем порт для FastAPI
EXPOSE 8000

# Команда для запуска FastAPI
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Сборка для фронтенда
FROM base AS frontend

# Устанавливаем рабочую директорию для фронтенда
WORKDIR /project/frontend

# Открываем порт для Streamlit
EXPOSE 8501

# Команда для запуска Streamlit
CMD ["poetry", "run", "streamlit", "run", "streamlit_ui.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

