import time
import os
import psycopg2
import sys

# URL do banco de dados
db_url = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/agency_accounting")

# Extrai as informações da URL
# Formato da URL: postgresql://user:password@host:port/dbname
user_pass, rest = db_url.split("@")[0].split("://")[1], db_url.split("@")[1]
user, password = user_pass.split(":")
host_port, dbname = rest.split("/")
host, port = host_port.split(":")

max_retries = 10
retry_interval = 5  # segundos

print(f"Tentando conectar a {host}:{port} banco {dbname} com usuário {user}")

for i in range(max_retries):
    try:
        print(f"Tentativa {i+1} de {max_retries}...")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            dbname=dbname
        )
        conn.close()
        print("Conexão com o banco de dados estabelecida com sucesso!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f"Erro ao conectar ao banco: {e}")
        if i < max_retries - 1:
            print(f"Aguardando {retry_interval} segundos antes de tentar novamente...")
            time.sleep(retry_interval)
        else:
            print("Número máximo de tentativas excedido. Não foi possível conectar ao banco.")
            sys.exit(1) 