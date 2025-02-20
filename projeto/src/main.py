import streamlit as st

st.set_page_config(
    page_title="Gestão Contábil - Agência",
    page_icon="📊",
    layout="wide"
)

st.title("Sistema de Gestão Contábil")

st.write("""
### Bem-vindo ao sistema!

Este é um projeto em desenvolvimento para gestão contábil de agência de publicidade.
""")

# Área para testar inputs
st.subheader("Teste de Funcionalidades")

# Input de texto simples
nome_cliente = st.text_input("Nome do Cliente")
if nome_cliente:
    st.write(f"Cliente digitado: {nome_cliente}")

# Teste de seleção de data
mes_referencia = st.date_input("Mês de Referência")
st.write(f"Data selecionada: {mes_referencia}")

# Teste de input numérico
valor = st.number_input("Valor do Serviço", min_value=0.0, format="%.2f")
if valor > 0:
    st.write(f"Valor digitado: R$ {valor:.2f}")