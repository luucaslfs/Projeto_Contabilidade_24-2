import streamlit as st
import pandas as pd
import sys
import os
import tempfile

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from import_excel import importar_plano_contas, importar_movimentacoes
from database import get_db
from models import MovimentacaoBancaria, PlanoContas

def main():
    st.title("Importação e Visualização de Dados")
    
    tabs = st.tabs(["Importação", "Movimentações", "Plano de Contas"])
    
    with tabs[0]:
        st.header("Importar Dados da Planilha Excel")
        
        uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            # Salva o arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Substitui os dois botões por um único botão para importar tudo
            if st.button("Importar Todos os Dados", type="primary"):
                with st.spinner("Importando dados..."):
                    # Primeiro importa o plano de contas
                    success_plano, message_plano = importar_plano_contas(tmp_path)
                    
                    if success_plano:
                        # Se plano foi importado com sucesso, importa as movimentações
                        success_mov, message_mov = importar_movimentacoes(tmp_path)
                        
                        # Exibe os resultados
                        st.write("### Resultado da importação:")
                        st.success(f"✅ Plano de Contas: {message_plano}")
                        
                        if success_mov:
                            st.success(f"✅ Movimentações: {message_mov}")
                        else:
                            st.error(f"❌ Movimentações: {message_mov}")
                    else:
                        st.error(f"❌ Erro na importação do Plano de Contas: {message_plano}")
                        st.warning("A importação das movimentações foi cancelada devido ao erro acima.")
            
            # Remove o arquivo temporário após o processamento
            os.unlink(tmp_path)
    
    with tabs[1]:
        st.header("Movimentações Bancárias")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filial = st.text_input("Filial", "")
        with col2:
            data_inicio = st.date_input("Data Início")
        with col3:
            data_fim = st.date_input("Data Fim")
        
        # Busca dados filtrados
        db = get_db()
        query = db.query(MovimentacaoBancaria)
        
        if filial:
            query = query.filter(MovimentacaoBancaria.filial.like(f"%{filial}%"))
        if data_inicio and data_fim:
            query = query.filter(MovimentacaoBancaria.data.between(data_inicio, data_fim))
        
        movimentacoes = query.limit(1000).all()  # Limita para melhorar performance
        
        if movimentacoes:
            # Converte para DataFrame para melhor visualização
            data = [{
                "ID": m.id,
                "Filial": m.filial,
                "Data": m.data,
                "Banco": m.banco,
                "Natureza": m.natureza,
                "Entrada": m.entrada if m.entrada else 0,
                "Saída": m.saida if m.saida else 0,
                "Histórico": m.historico
            } for m in movimentacoes]
            
            df = pd.DataFrame(data)
            st.dataframe(df)
            
            # Resumo
            st.subheader("Resumo")
            total_entradas = sum(m.entrada if m.entrada else 0 for m in movimentacoes)
            total_saidas = sum(m.saida if m.saida else 0 for m in movimentacoes)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Entradas", f"R$ {total_entradas:,.2f}")
            col2.metric("Total de Saídas", f"R$ {total_saidas:,.2f}")
            col3.metric("Saldo", f"R$ {total_entradas - total_saidas:,.2f}")
        else:
            st.info("Nenhuma movimentação encontrada com os filtros aplicados.")
        
        db.close()
    
    with tabs[2]:
        st.header("Plano de Contas")
        
        # Busca todas as contas
        db = get_db()
        contas = db.query(PlanoContas).all()
        
        if contas:
            # Converte para DataFrame
            data = [{
                "Código": c.codigo,
                "Descrição": c.descricao
            } for c in contas]
            
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.info("Nenhuma conta encontrada no plano de contas.")
        
        db.close()

if __name__ == "__main__":
    main()