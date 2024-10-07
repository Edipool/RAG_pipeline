"""
Этот модуль содержит утилиты для обработки загрузки файлов и создания индексов
с использованием Faiss и llama_index.
"""

import os
import shutil
from fastapi import UploadFile, HTTPException
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Директория для сохранения загруженных документов
UPLOAD_DIR = "data"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def process_upload(file: UploadFile):
    """
    Обрабатывает загрузку файла и создает индекс.

    Аргументы:
        file (UploadFile): Загружаемый файл.

    Возвращает:
        VectorStoreIndex: Индекс, созданный из загруженных документов.

    Исключения:
        HTTPException: Если файл имеет неподдерживаемое расширение или
        возникает ошибка при обработке.
    """
    try:
        # Проверка расширения файла
        if not (file.filename.endswith(".txt") or file.filename.endswith(".docx")):
            raise HTTPException(
                status_code=400, detail="Only .txt and .docx files are supported."
            )

        # Сохранение загруженного файла в директорию UPLOAD_DIR
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        # Чтение документов из директории
        reader = SimpleDirectoryReader(UPLOAD_DIR)
        documents = reader.load_data()

        # Инициализация Faiss индекса с размерностью для OpenAI embedding (1536 для text-ada-002)
        d = 1536
        faiss_index = faiss.IndexFlatL2(d)

        # Инициализация векторного хранилища FAISS
        faiss_store = FaissVectorStore(faiss_index=faiss_index)

        # Создание контекста хранения с использованием FAISS
        storage_context = StorageContext.from_defaults(vector_store=faiss_store)

        # Создание индекса из документов
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )

        return index

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading document: {str(e)}"
        )


def search_index(index, query: str):
    """
    Выполняет запрос поиска по индексу.

    Аргументы:
        index (VectorStoreIndex): Индекс для выполнения поиска.
        query (str): Строка поискового запроса.

    Возвращает:
        str: Ответ на поисковый запрос.

    Исключения:
        HTTPException: Если возникает ошибка при выполнении поиска.
    """
    try:
        # Выполнение запроса к индексу
        query_engine = index.as_query_engine()
        response = query_engine.query(query)

        return response.response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during search: {str(e)}")
