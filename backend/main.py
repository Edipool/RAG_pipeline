"""
Этот модуль реализует API для загрузки документов и выполнения поиска
с использованием FastAPI. Он включает в себя обработку загрузки файлов,
создание индекса и выполнение поисковых запросов.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from backend.contracts import SearchQuery
from backend.utils import process_upload, search_index
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Используем переменную окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Переменная для хранения индекса (на время тестов хранить локально индексы не будем).
index = None


@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """
    Загружает документ и создает индекс.

    Аргументы:
        file (UploadFile): Загружаемый файл.

    Возвращает:
        dict: Сообщение об успешной загрузке и индексации документа.
    """
    global index
    # Обработка загрузки файла и создание индекса
    index = process_upload(file)
    return {"message": f"Document '{file.filename}' uploaded and indexed successfully."}


@app.post("/search/")
async def search(query: SearchQuery):
    """
    Выполняет поиск по индексу.

    Аргументы:
        query (SearchQuery): Объект, содержащий строку поискового запроса.

    Возвращает:
        dict: Ответ на поисковый запрос.

    Исключения:
        HTTPException: Если индекс не создан.
    """
    global index
    if index is None:
        raise HTTPException(
            status_code=400,
            detail="Index is not created yet. Please upload documents first.",
        )

    # Выполнение поиска
    result = search_index(index, query.query)
    return {"response": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
