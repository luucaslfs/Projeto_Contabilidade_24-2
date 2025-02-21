# Sistema de Gestão Contábil - Agência de Publicidade

Sistema para controle financeiro de uma agência de publicidade, desenvolvido com Python, Streamlit e PostgreSQL.

## Stack Tecnológica

- **Frontend/Backend**: Python com Streamlit
- **Banco de Dados**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrações**: Alembic
- **Containerização**: Docker

## Preparando o Ambiente de Desenvolvimento

### Pré-requisitos

- Docker
- Docker Compose
- Git

### Instalação e Execução

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd <pasta-do-projeto>
```

2. Inicie o ambiente de desenvolvimento:
```bash
docker compose watch
```

O comando acima irá:
- Construir as imagens necessárias
- Iniciar os containers em modo de desenvolvimento
- Monitorar alterações nos arquivos e atualizar automaticamente
- Disponibilizar a aplicação em http://localhost:8501

### Desenvolvimento no Container

Para desenvolver diretamente no container (recomendado):

1. Em um novo terminal, acesse o container da aplicação:
```bash
docker compose exec web bash
```

2. Agora você pode executar comandos dentro do container, como:
```bash
# Acessar o Python
python

# Executar scripts
python src/script.py
```

### Trabalhando com Migrações do Banco de Dados

Todas as operações de migração devem ser executadas dentro do container:

1. Acesse o container:
```bash
docker compose exec web bash
```

2. Crie uma nova migração:
```bash
alembic revision --autogenerate -m "descricao_da_alteracao"
```

3. Aplique as migrações pendentes:
```bash
alembic upgrade head
```

4. Para reverter a última migração:
```bash
alembic downgrade -1
```

### Estrutura do Projeto

```
projeto/
├── docker-compose.yml    # Configuração dos serviços Docker
├── Dockerfile           # Configuração da imagem Python
├── requirements.txt     # Dependências Python
├── alembic.ini         # Configuração do Alembic
├── migrations/         # Arquivos de migração do banco
├── src/
│   ├── main.py         # Ponto de entrada da aplicação
│   ├── database.py     # Configuração do banco de dados
│   ├── models.py       # Modelos SQLAlchemy
│   ├── pages/          # Páginas Streamlit
│   └── utils/          # Funções auxiliares
└── README.md
```

### Hot Reload

O ambiente está configurado com hot reload para:

- **Arquivos Python**: Alterações são detectadas automaticamente
- **requirements.txt**: Container é reconstruído automaticamente se necessário

### Acessando o Sistema

- **Aplicação**: http://localhost:8501
- **Banco de Dados**: 
  - Host: localhost
  - Porta: 5432
  - Usuário: user
  - Senha: password
  - Banco: agency_accounting

## Regras de Negócio Implementadas

- Faturamento no mês seguinte ao serviço prestado
- Controle de despesas mensais
- Gestão de contratos com clientes
- Cálculo de horas por projeto

## Contribuindo

1. Crie uma branch para sua feature:
```bash
git checkout -b feature/nome-da-feature
```

2. Faça suas alterações e teste localmente

3. Commit suas mudanças:
```bash
git commit -m "Descrição clara da alteração"
```

4. Push para o repositório:
```bash
git push origin feature/nome-da-feature
```

## Boas Práticas

- Execute as migrações dentro do container
- Mantenha o código documentado
- Siga o padrão PEP 8
- Teste suas alterações antes de commit
- Mantenha o README atualizado