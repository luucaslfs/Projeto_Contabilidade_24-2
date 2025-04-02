FROM python:3.11-slim

WORKDIR /app

# Cria diretório para armazenar o banco SQLite
RUN mkdir -p /app/data && chmod 777 /app/data

COPY . .
RUN pip install -r requirements.txt

# Inicializa apenas as tabelas, sem inserir dados
RUN python src/init_db.py < /dev/null || echo "Banco será inicializado durante a execução"

# Executa a aplicação Streamlit
CMD ["streamlit", "run", "src/main.py"]