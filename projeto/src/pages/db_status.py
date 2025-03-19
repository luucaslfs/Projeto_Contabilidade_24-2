import streamlit as st
import sys
import os
import time
from datetime import datetime

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, DATABASE_URL
from sqlalchemy import text, inspect

st.set_page_config(
    page_title="Diagnóstico de Banco de Dados",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Diagnóstico de Conexão com Banco de Dados")

# Informações gerais
st.subheader("Informações Gerais")
col1, col2 = st.columns(2)

with col1:
    st.write("**URL de Conexão:**")
    # Mascara a senha na URL
    masked_url = DATABASE_URL
    if ":" in masked_url and "@" in masked_url:
        parts = masked_url.split("@")
        credentials = parts[0].split(":")
        if len(credentials) > 2:
            masked_url = f"{credentials[0]}:{'*' * 8}@{parts[1]}"
    
    st.code(masked_url)

with col2:
    st.write("**Data/Hora Atual:**")
    st.code(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# Teste de conexão
st.subheader("Teste de Conexão")

if st.button("Testar Conexão"):
    with st.spinner("Testando conexão com o banco..."):
        try:
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
            end_time = time.time()
            
            if row and row[0] == 1:
                st.success(f"✅ Conexão estabelecida com sucesso! (Tempo: {(end_time-start_time):.2f}s)")
            else:
                st.error(f"❌ Resultado inesperado: {row}")
        except Exception as e:
            st.error(f"❌ Erro ao conectar: {str(e)}")
            st.code(str(e))

# Informações do banco
st.subheader("Informações do Banco")

if st.button("Obter Metadados"):
    with st.spinner("Obtendo metadados do banco..."):
        try:
            # Tenta obter metadados do banco
            inspector = inspect(engine)
            
            # Lista as tabelas
            tables = inspector.get_table_names()
            
            if tables:
                st.success(f"✅ Conectado ao banco com {len(tables)} tabelas:")
                for table in tables:
                    with st.expander(f"Tabela: {table}"):
                        # Obtém as colunas
                        columns = inspector.get_columns(table)
                        st.write("**Colunas:**")
                        for column in columns:
                            st.write(f"- {column['name']} ({column['type']})")
            else:
                st.warning("⚠️ Banco conectado, mas sem tabelas!")
        except Exception as e:
            st.error(f"❌ Erro ao obter metadados: {str(e)}")
            st.code(str(e))

# Verificação de ambiente
st.subheader("Verificação de Ambiente")

# Verifica variáveis de ambiente
env_vars = {
    "DATABASE_URL": os.environ.get("DATABASE_URL", "Não definido"),
    "PYTHONPATH": os.environ.get("PYTHONPATH", "Não definido"),
    "PWD": os.environ.get("PWD", "Não definido"),
}

st.write("**Variáveis de Ambiente:**")
for key, value in env_vars.items():
    if key == "DATABASE_URL" and value != "Não definido":
        # Mascara a senha na URL
        if ":" in value and "@" in value:
            parts = value.split("@")
            credentials = parts[0].split(":")
            if len(credentials) > 2:
                value = f"{credentials[0]}:{'*' * 8}@{parts[1]}"
    st.code(f"{key}: {value}")

# Verifica dependências
st.write("**Versões de Dependências:**")
import sqlalchemy
import pandas as pd
import streamlit

dependencies = {
    "SQLAlchemy": sqlalchemy.__version__,
    "Pandas": pd.__version__,
    "Streamlit": streamlit.__version__,
    "Python": sys.version,
}

for key, value in dependencies.items():
    st.code(f"{key}: {value}")

# Informações sobre o Docker (se disponível)
st.subheader("Informações do Container")

try:
    with open('/proc/self/cgroup', 'r') as f:
        content = f.read()
        is_docker = 'docker' in content
        
    if is_docker:
        st.success("✅ Executando em um container Docker")
    else:
        st.warning("⚠️ Não parece estar executando em Docker")
except:
    st.info("ℹ️ Não foi possível determinar se está executando em Docker")

st.write("**Instruções para Debug:**")
st.info("""
1. Verifique se o container do PostgreSQL está rodando
2. Confira se as credenciais no DATABASE_URL estão corretas
3. Verifique as configurações de rede no docker-compose.yaml
4. Confira os logs do PostgreSQL para erros
""")

# Adiciona botão para reiniciar a página
if st.button("Reiniciar Diagnóstico"):
    st.experimental_rerun() 