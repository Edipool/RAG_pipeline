"""
Этот модуль реализует пользовательский интерфейс для системы Retrieval-Augmented Generation
с использованием Streamlit. Он позволяет загружать документы и выполнять поисковые запросы.
"""
import streamlit as st
import requests
import time

# URL API для взаимодействия с сервером
API_URL = "http://backend:8000"

# Инициализация состояния сессии
if 'document_uploaded' not in st.session_state:
    st.session_state.document_uploaded = False

if 'chat_id' not in st.session_state:
    # При первой загрузке создаем новый чат
    try:
        response = requests.post(f"{API_URL}/create_chat/")
        if response.status_code == 200:
            st.session_state.chat_id = response.json()["chat_id"]
        else:
            st.session_state.chat_id = None
    except Exception:
        st.session_state.chat_id = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Заголовок приложения
st.title("Retrieval-Augmented Generation System")

# Боковая панель с описанием
with st.sidebar:
    st.header("О системе")
    st.info(
        "Эта система позволяет:\n"
        "1. Загружать документы (.txt или .docx)\n"
        "2. Выполнять поиск по документам\n"
        "3. Генерировать ответы на основе контекста из документов"
    )

    st.header("Режимы работы")
    st.write("**Поиск**: поиск по индексированным документам")
    st.write("**Генерация**: поиск с генерацией ответа на основе найденных документов")

    # Добавляем кнопку для создания нового чата
    if st.button("Начать новый чат"):
        try:
            response = requests.post(f"{API_URL}/create_chat/")
            if response.status_code == 200:
                st.session_state.chat_id = response.json()["chat_id"]
                st.session_state.chat_history = []
                st.success("Создан новый чат!")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"Ошибка при создании нового чата: {str(e)}")

    if st.session_state.chat_id:
        st.info(f"Текущий ID чата: {st.session_state.chat_id[:8]}...")

# Секция загрузки файла
with st.expander("Document Upload", expanded=not st.session_state.document_uploaded):
    # Загрузка файла пользователем
    uploaded_file = st.file_uploader("Choose a file (.txt or .docx)", type=["txt", "docx"])

    # Добавляем кнопку для явной загрузки файла
    if uploaded_file is not None and st.button("Upload Document"):
        # Показать индикатор загрузки
        with st.spinner("Uploading document..."):
            # Подготовка файла для отправки на сервер
            files = {"file": uploaded_file}
            # Отправка POST-запроса для загрузки файла
            response = requests.post(f"{API_URL}/upload/", files=files)
            # Проверка статуса ответа
            if response.status_code == 200:
                st.success("Document uploaded and indexed successfully")
                st.session_state.document_uploaded = True
                st.rerun()  # Перезагружаем страницу для обновления состояния
            else:
                st.error(f"Failed to upload document: {response.json().get('detail')}")

# Отображаем статус загрузки документа
if st.session_state.document_uploaded:
    st.success("Document is uploaded and indexed. You can search or generate answers now.")
else:
    st.warning("Please upload a document first.")

# Если документ загружен, показываем интерфейс для запросов
if st.session_state.document_uploaded:
    # Выбор режима работы
    mode = st.radio("Select mode:", ["Chat", "Search"])

    # Отображение истории чата
    if mode == "Chat" and st.session_state.chat_history:
        st.subheader("Chat History")
        chat_container = st.container()

        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You**: {message['content']}")
                else:
                    st.markdown(f"**Assistant**: {message['content']}")
                st.divider()

    # Ввод поискового запроса пользователем
    query = st.text_input("Enter your query")

    # Если выбран режим чата
    if mode == "Chat":
        with st.expander("Advanced settings", expanded=False):
            max_tokens = st.slider("Max tokens for response", 100, 2000, 1000)
            use_memory = st.checkbox("Use chat memory", value=True)

        # Кнопка для отправки запроса
        if st.button("Send"):
            if query:
                # Добавляем запрос пользователя в историю чата
                st.session_state.chat_history.append({"role": "user", "content": query})

                # Показать индикатор генерации
                with st.spinner("Generating response..."):
                    # Подготовка данных для запроса
                    request_data = {
                        "query": query,
                        "max_tokens": max_tokens
                    }

                    # Добавляем chat_id, если включена память чата
                    if use_memory and st.session_state.chat_id:
                        request_data["chat_id"] = st.session_state.chat_id

                    # Отправка POST-запроса для генерации ответа
                    try:
                        response = requests.post(
                            f"{API_URL}/generate/",
                            json=request_data
                        )

                        # Проверка статуса ответа
                        if response.status_code == 200:
                            result = response.json()
                            answer = result["answer"]

                            # Добавляем ответ в историю чата
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})

                            # Сохраняем источники в сессии
                            st.session_state.last_sources = result["sources"]

                            # Перезагружаем страницу для обновления интерфейса
                            st.rerun()
                        else:
                            st.error(f"Generation failed: {response.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error during generation: {str(e)}")

        # Показываем источники последнего ответа, если они есть
        if 'last_sources' in st.session_state and st.session_state.last_sources:
            with st.expander("Last Answer Sources", expanded=False):
                for i, source in enumerate(st.session_state.last_sources):
                    st.markdown(f"**Source {i+1}** (score: {source['score']:.2f})")
                    st.text(source["text"])
                    st.divider()

    # Если выбран режим поиска
    elif mode == "Search":
        # Кнопка для запуска поиска
        if st.button("Search"):
            if query:
                # Показать индикатор поиска
                with st.spinner("Searching..."):
                    # Отправка POST-запроса для выполнения поиска
                    response = requests.post(f"{API_URL}/search/", json={"query": query})
                    # Проверка статуса ответа
                    if response.status_code == 200:
                        result = response.json()["response"]
                        st.subheader("Search Results")
                        st.write(result)
                    else:
                        st.error(f"Search failed: {response.json().get('detail')}")

# Добавляем информацию о реализации RAG
st.divider()
st.caption("Retrieval-Augmented Generation (RAG) Pipeline | Made with FastAPI, Llama Index, and Streamlit")
