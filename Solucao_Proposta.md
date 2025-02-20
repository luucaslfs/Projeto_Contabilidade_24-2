## Solução Proposta

### Estrutura do Sistema
- Aplicação Python única usando Streamlit para interface e processamento
- Banco de dados PostgreSQL para persistência
- Containers Docker para desenvolvimento e execução

### Funcionalidades

#### Dashboard Interativo (Streamlit)
- Páginas separadas para:
  - Cadastro/Edição de dados
  - Visualização de métricas e gráficos
  - Geração de relatórios
- Componentes principais:
  - Formulários para entrada de dados
  - Gráficos interativos usando Plotly
  - Filtros de período usando componentes nativos do Streamlit
  - Tabelas dinâmicas para visualização detalhada

#### Relatórios
- Geração automatizada usando pandas
- Exportação para Excel/PDF
- Visualização na própria interface

### Tecnologias
- Streamlit: Interface web e lógica de negócio
- PostgreSQL: Banco de dados
- SQLAlchemy: ORM para manipulação do banco
- Pandas: Processamento de dados
- Plotly: Visualizações gráficas
- Docker: Containerização
- Docker Compose: Orquestração local

### Estrutura do Projeto
```
projeto/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── src/
│   ├── main.py          # Aplicação Streamlit
│   ├── database.py      # Configuração do banco
│   ├── models.py        # Modelos SQLAlchemy
│   ├── pages/          
│   │   ├── cadastro.py  # Página de entrada de dados
│   │   ├── dashboard.py # Página de visualizações
│   │   └── relatorios.py# Página de relatórios
│   └── utils/
│       ├── graficos.py  # Funções para gerar gráficos
│       └── relatorios.py# Funções para gerar relatórios
└── README.md
```

## Entregáveis
1. Aplicação Streamlit containerizada
2. Banco de dados PostgreSQL configurado
3. Interface para entrada e visualização de dados
4. Sistema de relatórios integrado
5. Documentação de instalação e uso