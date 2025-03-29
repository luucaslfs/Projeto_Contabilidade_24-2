import streamlit as st

st.set_page_config(
    page_title="Gestão Contábil - Agência",
    page_icon="📊",
    layout="wide"
)

st.title("Sistema de Gestão Contábil para Agência de Publicidade")

st.write("""
O sistema permite analisar dados financeiros da agência, com foco em:
- Análise Vertical de receitas e despesas
- Classificação de custos fixos e variáveis
- Índices financeiros e de liquidez
- Análise de tendências e sazonalidade
""")

# Cards para navegação rápida
st.markdown("### Acesso Rápido às Funcionalidades")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    ### 📥 Importação de Dados
    
    Importe seus dados financeiros de planilhas CSV para análise no sistema.
    
    - Movimentações bancárias
    - Plano de contas
    - Categorizações automáticas
    """)
    
    if st.button("Importar Dados", type="primary", key="import"):
        st.switch_page("pages/Importar_Dados.py")

with col2:
    st.success("""
    ### 📊 Dashboard Financeiro
    
    Visualize métricas e gráficos baseados nos conceitos contábeis.
    
    - Indicadores financeiros
    - Análise vertical
    - Estrutura de custos
    - Tendências de faturamento
    """)
    
    if st.button("Acessar Dashboard", type="primary", key="dashboard"):
        st.switch_page("pages/Dashboard_Financeiro.py")

# Seção de conceitos contábeis aplicados
st.markdown("---")
st.markdown("## Conceitos Contábeis Aplicados")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Pereira da Silva (2017)
    
    - **Análise Vertical**: Representa cada componente financeiro como percentual de um valor base (receita total)
    
    - **Margem Líquida**: Percentual da receita que se converte em lucro após despesas
    
    - **Análise de Liquidez**: Capacidade da empresa de honrar seus compromissos financeiros
    
    - **Análise de Tendência**: Evolução dos indicadores financeiros ao longo do tempo
    """)

with col2:
    st.markdown("""
    ### Martins (2018)
    
    - **Custos Fixos vs. Variáveis**: Classificação dos custos conforme sua relação com o volume de serviços
    
    - **Índice de Fixação**: Proporção de custos fixos em relação ao total, indicando rigidez operacional
    
    - **Análise de Produtividade**: Métricas como receita por hora e custo por serviço
    
    - **Composição de Custos**: Estrutura de custos e seu impacto nas decisões gerenciais
    """)

# Rodapé com informações adicionais
st.markdown("---")
st.markdown("""
### Relatórios Disponíveis

O sistema permite gerar relatórios detalhados a partir dos dados analisados:

- **Demonstrativo de Resultado**: Análise vertical de receitas e despesas
- **Análise de Custos**: Custos fixos vs. variáveis e índice de fixação
- **Relatório de Faturamento**: Evolução mensal e por tipo de serviço
- **Índices Financeiros**: Margem, liquidez e produtividade

Para gerar relatórios, acesse o Dashboard Financeiro e clique no botão "Gerar Relatório PDF" no menu lateral.
""")

st.caption("© 2025 Sistema de Gestão Contábil - Projeto Acadêmico")