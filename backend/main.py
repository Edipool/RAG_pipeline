"""
Этот модуль реализует API для загрузки документов и выполнения поиска
с использованием FastAPI. Он включает в себя обработку загрузки файлов,
создание индекса и выполнение поисковых запросов.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from backend.contracts import SearchQuery, GenerateQuery
from backend.utils import process_upload, search_index, generate_answer, get_or_create_chat_id
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Загружаем переменные из .env файла
load_dotenv()

# Используем переменную окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Переменная для хранения индекса (на время тестов хранить локально индексы не будем).
index = None

class CreateChatResponse(BaseModel):
    """Ответ на запрос создания нового чата"""
    chat_id: str

@app.post("/create_chat/")
async def create_chat() -> CreateChatResponse:
    """
    Создает новый чат и возвращает его идентификатор.

    Возвращает:
        CreateChatResponse: Объект с идентификатором чата.
    """
    chat_id = get_or_create_chat_id()
    return CreateChatResponse(chat_id=chat_id)

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


@app.post("/generate/")
async def generate(query: GenerateQuery):
    """
    Генерирует ответ на основе результатов поиска по индексу,
    с учетом истории диалога, если указан chat_id.

    Аргументы:
        query (GenerateQuery): Объект, содержащий строку запроса и параметры генерации.

    Возвращает:
        dict: Сгенерированный ответ и источники информации.

    Исключения:
        HTTPException: Если индекс не создан.
    """
    global index
    if index is None:
        raise HTTPException(
            status_code=400,
            detail="Index is not created yet. Please upload documents first.",
        )

    # Выполнение генерации ответа с учетом системного промпта и chat_id
    result = generate_answer(
        index,
        query.query,
        query.max_tokens,
        query.system_prompt,
        query.chat_id
    )
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
