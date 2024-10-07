"""
Этот модуль реализует пользовательский интерфейс для системы Retrieval-Augmented Generation
с использованием Streamlit. Он позволяет загружать документы и выполнять поисковые запросы.
"""

import streamlit as st
import requests

# URL API для взаимодействия с сервером
API_URL = "http://localhost:8000"

# Заголовок приложения
st.title("Retrieval-Augmented Generation System")

# Загрузка файла пользователем
uploaded_file = st.file_uploader("Choose a file (.txt or .docx)", type=["txt", "docx"])
if uploaded_file is not None:
    # Показать индикатор загрузки
    with st.spinner("Uploading document..."):
        # Подготовка файла для отправки на сервер
        files = {"file": uploaded_file}
        # Отправка POST-запроса для загрузки файла
        response = requests.post(f"{API_URL}/upload/", files=files)
        # Проверка статуса ответа
        if response.status_code == 200:
            st.success("Document uploaded and indexed successfully")
        else:
            st.error(f"Failed to upload document: {response.json().get('detail')}")

# Ввод поискового запроса пользователем
query = st.text_input("Enter your search query")
if st.button("Search"):
    if query:
        # Показать индикатор поиска
        with st.spinner("Searching..."):
            # Отправка POST-запроса для выполнения поиска
            response = requests.post(f"{API_URL}/search/", json={"query": query})
            # Проверка статуса ответа
            if response.status_code == 200:
                result = response.json()["response"]
                st.write(result)
            else:
                st.error(f"Search failed: {response.json().get('detail')}")
