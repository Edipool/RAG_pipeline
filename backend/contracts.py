"""
В этом модуле определены контракты для взаимодействия с поисковой системой.
"""

from pydantic import BaseModel
from typing import Optional

class SearchQuery(BaseModel):
    """
    Модель для представления поискового запроса.

    Атрибуты:
        query (str): Строка, содержащая текст поискового запроса.
    """
    query: str

class GenerateQuery(BaseModel):
    """
    Модель для представления запроса на генерацию ответа.

    Атрибуты:
        query (str): Строка, содержащая текст запроса.
        max_tokens (int): Максимальное количество токенов для генерации ответа.
        system_prompt (str, optional): Системный промпт для модели. Если не указан, будет использоваться промпт по умолчанию.
        chat_id (str, optional): Идентификатор чата для отслеживания истории разговора.
    """
    query: str
    max_tokens: int = 1000
    system_prompt: Optional[str] = None
    chat_id: Optional[str] = None
