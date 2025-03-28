import streamlit as st

st.set_page_config(
    page_title="Gestão Contábil - Agência",
    page_icon="📊",
    layout="wide"
)

st.title("Sistema de Gestão Contábil para Agência de Publicidade")

st.write("""
### Bem-vindo ao sistema!

Este projeto gerencia a contabilidade para agências de publicidade, implementando conceitos de:

- **Pereira da Silva, J.** - "Análise Financeira das Empresas" (13ª edição, Cengage Learning, 2017)
- **Martins, E.** - "Contabilidade de Custos" (11ª edição, GEN/Atlas, 2018)

O sistema permite controlar:
- Receitas e despesas
- Análise de custos fixos e variáveis
- Visualização de indicadores financeiros
- Relatórios contábeis
""")

# Cards de navegação rápida
st.subheader("Navegação Rápida")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("📊 **Dashboard Financeiro**\n\nVisualize métricas, gráficos e indicadores financeiros baseados nos conceitos de contabilidade estudados.")
    if st.button("Acessar Dashboard", key="dashboard"):
        st.switch_page("pages/dashboard_financeiro.py")

with col2:
    st.info("👥 **Cadastro de Clientes**\n\nGerencie os dados dos seus clientes e veja todos os registros.")
    if st.button("Gerenciar Clientes", key="clientes"):
        st.switch_page("pages/cadastro_cliente.py")

with col3:
    st.info("📋 **Importação de Dados**\n\nImporte dados de planilhas e visualize movimentações bancárias.")
    if st.button("Importar Dados", key="importar"):
        st.switch_page("pages/importacao_dados.py")

# Segunda linha de cards
col1, col2 = st.columns(2)

with col1:
    st.info("🔍 **Status do Banco**\n\nVerifique a conexão e o status do banco de dados.")
    if st.button("Verificar Banco", key="banco"):
        st.switch_page("pages/db_status.py")

with col2:
    st.success("📚 **Conceitos Aplicados**\n\nO sistema implementa diversos conceitos contábeis como análise vertical, classificação de custos fixos e variáveis, fluxo de caixa e indicadores financeiros.")

# Rodapé com referências bibliográficas
st.markdown("---")
st.write("""
### Funcionalidades Implementadas:

- **Análise Vertical**: Baseada em Pereira da Silva (2017)
- **Classificação de Custos**: Fixos vs. Variáveis (Martins, 2018)
- **Índice de Fixação de Despesas**: Indicador de rigidez operacional 
- **Fluxo de Caixa**: Monitoramento de entradas, saídas e saldo acumulado
- **Visualizações**: Gráficos interativos para análise financeira
""")

st.caption("Projeto de Gestão Contábil - Agência de Publicidade © 2025")