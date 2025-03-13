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
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.response_synthesizers import get_response_synthesizer

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


def generate_answer(index, query: str, max_tokens: int = 1000):
    """
    Генерирует ответ на основе контекста, полученного из поиска по индексу.

    Аргументы:
        index (VectorStoreIndex): Индекс для выполнения поиска.
        query (str): Строка поискового запроса.
        max_tokens (int): Максимальное количество токенов для генерации ответа.

    Возвращает:
        dict: Словарь, содержащий сгенерированный ответ и найденные источники.

    Исключения:
        HTTPException: Если возникает ошибка при выполнении поиска или генерации.
    """
    try:
        # Настраиваем LLM
        llm = OpenAI(model="gpt-4o-mini", max_tokens=max_tokens)
        Settings.llm = llm

        # Создаем поисковый движок, который будет искать по индексу
        retriever = index.as_retriever(similarity_top_k=3)

        # Получаем релевантные куски текста
        retrieved_nodes = retriever.retrieve(query)

        # Формируем сообщение с контекстом
        context_text = "\n\n".join([node.get_content() for node in retrieved_nodes])

        # Создаем синтезатор ответов
        response_synthesizer = get_response_synthesizer(
            response_mode="refine",
            llm=llm
        )

        # Генерируем ответ на основе найденных источников
        response = response_synthesizer.synthesize(
            query=query,
            nodes=retrieved_nodes
        )

        # Возвращаем ответ и источники
        sources = [{"text": node.get_content(), "score": node.get_score()} for node in retrieved_nodes]

        return {
            "answer": response.response,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during answer generation: {str(e)}"
        )
