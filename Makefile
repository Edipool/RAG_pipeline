# Run backend
back:
	uvicorn backend.main:app --reload
# Run frontend
front:
	streamlit run frontend/streamlit_ui.py
