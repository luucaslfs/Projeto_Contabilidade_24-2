import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# Define o caminho para o arquivo SQLite
# O arquivo será criado na pasta 'data' dentro do diretório atual
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(data_dir, exist_ok=True)
sqlite_file = os.path.join(data_dir, 'agency_accounting.db')

# Usa SQLite por padrão, mas permite sobrescrever via variável de ambiente
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{sqlite_file}')

# Verifica se é PostgreSQL (para compatibilidade caso queira voltar)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configura o engine do SQLAlchemy com as opções corretas para cada banco
is_sqlite = DATABASE_URL.startswith('sqlite')
connect_args = {'check_same_thread': False} if is_sqlite else {'connect_timeout': 10}

# Cria o engine com as configurações apropriadas
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Não mostra queries no console (mude para True para debugging)
    pool_pre_ping=True,  # Verifica se a conexão está ativa
    pool_recycle=3600,  # Recicla conexões após 1 hora
    connect_args=connect_args
)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Função para obter uma sessão do banco de dados"""
    db = SessionLocal()
    return db

def test_connection():
    """Função para testar a conexão com o banco"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"Tentativa {attempt+1} de {max_attempts} - Conectando ao banco usando: {DATABASE_URL}")
            # Usando text() para criar uma consulta SQL com SQLAlchemy 2.0
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                # Verificando se há resultado
                row = result.fetchone()
                if row and row[0] == 1:
                    print(f"✅ Conexão com o banco de dados estabelecida com sucesso! (tentativa {attempt+1})")
                    return True
                else:
                    print(f"❌ Resultado inesperado: {row}")
                    return False
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco (tentativa {attempt+1}): {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_attempts - 1:
                print(f"⏳ Aguardando 2 segundos antes de tentar novamente...")
                time.sleep(2)
    
    print("❌ Todas as tentativas de conexão falharam")
    return False

# Define variáveis globais para indicar o tipo de banco em uso
IS_SQLITE = is_sqlite
DB_TYPE = "SQLite" if is_sqlite else "PostgreSQL"

# Exporta as entidades principais
__all__ = ['engine', 'DATABASE_URL', 'get_db', 'test_connection', 'IS_SQLITE', 'DB_TYPE']