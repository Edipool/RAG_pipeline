# Retrieval-Augmented Generation (RAG) Pipeline

Этот проект представляет собой систему для загрузки документов, их индексации и поиска с использованием подхода Retrieval-Augmented Generation (RAG), но без генерации ответов. Веб-интерфейс на базе **Streamlit** позволяет пользователям загружать текстовые документы и выполнять поиск по ним. Для обработки данных используются **FastAPI**, **Llama_index** и **Faiss**.

## Описание проекта

В рамках данного проекта реализована система RAG, где:
- Пользователь загружает текстовые документы (например, `.txt` или `.docx`).
- Документы индексируются для последующего поиска.
- Пользователь может делать поисковые запросы, а система возвращает результаты на основе загруженных документов.

Система построена с использованием:
- **FastAPI + Llama_index + Faiss** — для реализации REST API и поиска по векторной базе данных.
- **Streamlit** — для создания пользовательского интерфейса.

## Запуск проекта

### 1. Клонирование репозитория

```bash
git clone https://github.com/Edipool/RAG_pipeline.git
```

### 2. Запуск проекта с помощью Docker Compose

Находясь в корневой папке проекта, выполните следующую команду:

```bash
OPENAI_API_KEY=ваш_ключ_от_openai_без_кавычек docker-compose up --build
```

После сборки и запуска проекта в консоли будут указаны два адреса:
- `http://0.0.0.0:8501` — веб-интерфейс (UI)
- `http://0.0.0.0:8000/docs` — документация FastAPI

Перейдя по адресу UI, вы сможете загрузить файл и выполнить поисковый запрос по загруженным документам.

## Структура проекта

```
.
├── backend
│   ├── contracts.py    # Описание API контрактов.
│   ├── main.py         # Логика FastAPI для загрузки и поиска.
│   ├── utils.py        # Утилиты для обработки файлов и выполнения поиска.
│   └── __init__.py
├── frontend
│   ├── streamlit_ui.py # Интерфейс на базе Streamlit для загрузки и поиска.
│   └── __init__.py
├── poetry.lock
├── pyproject.toml      # Конфигурационный файл для Poetry.
├── docker-compose.yml  # Конфигурация Docker Compose для управления контейнерами.
├── Dockerfile          # Dockerfile для сборки образов бэкенда и фронтенда.
└── README.md
```

## Что ещё можно было сделать?

За 8 часов был разработан MVP (минимально жизнеспособный продукт). В течение этих 8 часов было сделано следующее:
1. 2 часа ушло на изучение документации и знакомство с **Llama_index** (до этого использовался только **LangChain**).
2. 3 часа потребовалось на разработку и отладку бэкенда.
3. 1 час был затрачен на создание пользовательского интерфейса.
4. 1 час ушёл на контейнеризацию.
5. 1 час был посвящён отладке, тестированию и описанию проекта.

### Возможные улучшения:
1. Реализовать более осмысленное разбиение текста, используя подход *[Semantic Chunking](https://docs.llamaindex.ai/en/stable/examples/node_parsers/semantic_chunking/)*.
2. Добавить тесты.
3. Написать документацию с использованием Sphinx.
4. Добавить мониторинг и метрики с помощью Prometheus и Grafana.
5. Провести эксперименты с различными типами ретриверов: косинусное расстояние, BM25 и их комбинации.
6. Добавить более информативные ответы от поисковой системы, например, указать, из какого документа был возвращён ответ.
7. Настроить локальное сохранение индексов (сейчас они хранятся в ОЗУ).
8. Оптимизировать процесс поиска, так как при загрузке файла и нажатии на кнопку "поиск" происходит повторная загрузка уже загруженного файла.
