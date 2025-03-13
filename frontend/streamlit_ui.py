"""
Этот модуль реализует пользовательский интерфейс для системы Retrieval-Augmented Generation
с использованием Streamlit. Он позволяет загружать документы и выполнять поисковые запросы.
"""
import streamlit as st
import requests

# URL API для взаимодействия с сервером
API_URL = "http://backend:8000"

# Инициализация состояния сессии
if 'document_uploaded' not in st.session_state:
    st.session_state.document_uploaded = False

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
    mode = st.radio("Select mode:", ["Search", "Generate"])

    # Ввод поискового запроса пользователем
    query = st.text_input("Enter your query")

    # Если выбран режим генерации, показать дополнительные настройки
    if mode == "Generate":
        with st.expander("Advanced settings", expanded=False):
            max_tokens = st.slider("Max tokens for response", 100, 2000, 1000)

        # Кнопка для запуска генерации
        if st.button("Generate"):
            if query:
                # Показать индикатор генерации
                with st.spinner("Generating response..."):
                    # Отправка POST-запроса для генерации ответа
                    response = requests.post(
                        f"{API_URL}/generate/",
                        json={"query": query, "max_tokens": max_tokens}
                    )
                    # Проверка статуса ответа
                    if response.status_code == 200:
                        result = response.json()
                        # Отображение сгенерированного ответа
                        st.subheader("Generated Answer")
                        st.write(result["answer"])

                        # Отображение источников информации
                        with st.expander("Sources", expanded=False):
                            for i, source in enumerate(result["sources"]):
                                st.markdown(f"**Source {i+1}** (score: {source['score']:.2f})")
                                st.text(source["text"])
                                st.divider()
                    else:
                        st.error(f"Generation failed: {response.json().get('detail')}")

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
