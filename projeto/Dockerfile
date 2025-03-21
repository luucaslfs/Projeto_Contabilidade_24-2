FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary

# Executa diretamente a aplicação Streamlit sem inicializar o banco
CMD ["streamlit", "run", "src/main.py"]