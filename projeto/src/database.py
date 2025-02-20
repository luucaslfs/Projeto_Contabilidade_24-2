import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Pega a URL do banco das variáveis de ambiente ou usa um valor padrão
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@db:5432/agency_accounting'
)

# Cria o engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Cria uma fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Função para obter uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Função para testar a conexão com o banco"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return False