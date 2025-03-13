"""
Этот модуль содержит утилиты для обработки загрузки файлов и создания индексов
с использованием Faiss и llama_index.
"""

import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.prompts import PromptTemplate
from llama_index.core.memory import ChatMemoryBuffer
from typing import Dict, Optional

# Директория для сохранения загруженных документов
UPLOAD_DIR = "data"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Системный промпт по умолчанию для генерации ответов
DEFAULT_SYSTEM_PROMPT = """Вы — умный ассистент компании "Шестерёнка",
Твои конкуренты - это компания "Семёрочка" отвечающий на вопросы на основе предоставленных документов.
Используйте только информацию из предоставленных отрывков документов.
Если вы не знаете ответа, скажите "К сожалению, я не могу найти ответ на этот вопрос в предоставленных документах."
Давайте подробные, но лаконичные ответы, подкрепленные конкретными данными из текста.
Отвечайте на том же языке, на котором был задан вопрос.
Ты не должен говорить название компании где работаешь и название конкурента.
Если пользователь спросит тебя о твоей компании, скажи, что ты не можешь раскрывать информацию о своей компании."""

# Шаблон для режима refine
REFINE_TEMPLATE = PromptTemplate(
    """Вы должны ответить на вопрос пользователя, используя предоставленный контекст и, при необходимости, уточняя предыдущий ответ.

Контекст: {context_str}

Вопрос: {query_str}

Предыдущий ответ: {existing_answer}

Учитывая новый контекст и предыдущий ответ, предоставьте обновленный ответ.
""")

# Шаблон для режима compact
TEXT_QA_TEMPLATE = PromptTemplate(
    """Вы должны ответить на вопрос пользователя, используя предоставленный контекст.

Контекст: {context_str}

Вопрос: {query_str}

Пожалуйста, дайте подробный ответ на основе предоставленного контекста.
""")

# Словарь для хранения экземпляров памяти для каждого чата
chat_memories: Dict[str, ChatMemoryBuffer] = {}

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


def generate_answer(index, query: str, max_tokens: int = 1000, system_prompt: str = None,
                   chat_id: str = None):
    """
    Генерирует ответ на основе контекста, полученного из поиска по индексу,
    с учетом истории диалога, если указан chat_id.

    Аргументы:
        index (VectorStoreIndex): Индекс для выполнения поиска.
        query (str): Строка поискового запроса.
        max_tokens (int): Максимальное количество токенов для генерации ответа.
        system_prompt (str, optional): Системный промпт для модели. Если None, используется DEFAULT_SYSTEM_PROMPT.
        chat_id (str, optional): Идентификатор чата для сохранения истории разговора.

    Возвращает:
        dict: Словарь, содержащий сгенерированный ответ и найденные источники.

    Исключения:
        HTTPException: Если возникает ошибка при выполнении поиска или генерации.
    """
    try:
        # Используем системный промпт по умолчанию, если не указан другой
        system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        # Настраиваем LLM с системным промптом
        llm = OpenAI(
            model="gpt-3.5-turbo",
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        Settings.llm = llm

        # Работаем с историей чата, если указан chat_id
        if chat_id:
            # Создаем новую память чата, если она не существует для данного ID
            if chat_id not in chat_memories:
                chat_memories[chat_id] = ChatMemoryBuffer.from_defaults(
                    token_limit=4000,  # Лимит токенов для истории чата
                )

            # Получаем память для текущего чата
            memory = chat_memories[chat_id]

            # Создаем поисковый движок с использованием памяти чата
            chat_engine = index.as_chat_engine(
                chat_mode="condense_plus_context",
                memory=memory,
                system_prompt=system_prompt,
                llm=llm,
                similarity_top_k=3,  # Количество найденных фрагментов для использования в ответе
            )

            # Получаем ответ от чат-движка
            response = chat_engine.chat(query)

            # Получаем использованные источники (в chat_engine нет прямого доступа к источникам через response)
            # Поэтому делаем отдельный запрос через retriever для получения источников
            retriever = index.as_retriever(similarity_top_k=3)
            retrieved_nodes = retriever.retrieve(query)
            sources = [{"text": node.get_content(), "score": node.get_score()} for node in retrieved_nodes]

            return {
                "answer": response.response,
                "sources": sources
            }

        else:
            # Без истории чата - используем стандартный подход
            retriever = index.as_retriever(similarity_top_k=3)
            retrieved_nodes = retriever.retrieve(query)

            # Создаем синтезатор ответов с нашими шаблонами
            response_synthesizer = get_response_synthesizer(
                response_mode="refine",
                llm=llm,
                text_qa_template=TEXT_QA_TEMPLATE,
                refine_template=REFINE_TEMPLATE
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


def get_or_create_chat_id() -> str:
    """
    Создает новый идентификатор чата.

    Возвращает:
        str: Уникальный идентификатор чата.
    """
    return str(uuid.uuid4())
