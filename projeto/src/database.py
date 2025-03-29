import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# Pega a URL do banco das variáveis de ambiente ou usa um valor padrão
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@db:5432/agency_accounting'
)

# Cria o engine do SQLAlchemy com parâmetros adicionais
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Não mostra queries no console (mude para True para debugging)
    pool_pre_ping=True,  # Verifica se a conexão está ativa
    pool_recycle=3600,  # Recicla conexões após 1 hora
    connect_args={"connect_timeout": 10}  # Timeout de conexão
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

# Exporta as entidades principais
__all__ = ['engine', 'DATABASE_URL', 'get_db', 'test_connection']