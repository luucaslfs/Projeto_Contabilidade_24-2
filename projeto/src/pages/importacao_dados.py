import streamlit as st
import pandas as pd
import sys
import os
import tempfile
from datetime import datetime

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa as funções melhoradas
from import_excel import importar_plano_contas, importar_movimentacoes
from database import get_db, test_connection
from models import MovimentacaoBancaria, PlanoContas

def main():
    st.title("Importação de Dados CSV")
    
    # Verifica a conexão com o banco
    with st.spinner("Verificando conexão com o banco de dados..."):
        connection_result = test_connection()
    
    if not connection_result:
        st.error("❌ Não foi possível conectar ao banco de dados!")
        return
    
    st.write("""
    ### Importação de Movimentações Bancárias
    
    Este módulo permite importar dados de movimentações bancárias a partir de um arquivo CSV.
    O arquivo deve conter as seguintes colunas:
    
    - Filial Orig
    - Data
    - Banco
    - Agencia
    - Conta Banco
    - Natureza
    - Nome Natureza
    - Documento
    - Entrada
    - Saida
    - Historico
    """)
    
    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Visualiza primeiras linhas
            df_preview = pd.read_csv(uploaded_file, encoding='utf-8', nrows=5)
            
            st.subheader("Prévia dos Dados")
            st.dataframe(df_preview)
            
            # Verifica colunas obrigatórias
            required_columns = ['Filial Orig', 'Data', 'Banco', 'Natureza', 'Nome Natureza', 'Entrada', 'Saida', 'Historico']
            missing_columns = [col for col in required_columns if col not in df_preview.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
            else:
                # Salva temporariamente para processamento
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # Botão para importar
                if st.button("Importar Dados", type="primary"):
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
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
    
    # Exibe informações sobre os dados já importados
    st.subheader("Dados Atualmente Importados")
    
    db = get_db()
    try:
        # Conta registros nas tabelas
        plano_contas_count = db.query(PlanoContas).count()
        movimentacoes_count = db.query(MovimentacaoBancaria).count()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Plano de Contas", f"{plano_contas_count} registros")
        
        with col2:
            st.metric("Movimentações Bancárias", f"{movimentacoes_count} registros")
        
        # Se há movimentações, mostra um resumo
        if movimentacoes_count > 0:
            # Data da movimentação mais recente
            ultima_mov = db.query(MovimentacaoBancaria).order_by(MovimentacaoBancaria.data.desc()).first()
            primeira_mov = db.query(MovimentacaoBancaria).order_by(MovimentacaoBancaria.data.asc()).first()
            
            # Soma de entradas e saídas
            totais = db.query(
                db.func.sum(MovimentacaoBancaria.entrada).label("total_entradas"),
                db.func.sum(MovimentacaoBancaria.saida).label("total_saidas")
            ).one()
            
            st.write("### Resumo das Movimentações")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Período", f"{primeira_mov.data.strftime('%d/%m/%Y')} a {ultima_mov.data.strftime('%d/%m/%Y')}")
            
            with col2:
                st.metric("Total de Entradas", f"R$ {totais.total_entradas:,.2f}")
            
            with col3:
                st.metric("Total de Saídas", f"R$ {totais.total_saidas:,.2f}")
            
            # Categorias de naturezas
            categorias = db.query(
                MovimentacaoBancaria.categoria,
                db.func.count(MovimentacaoBancaria.id).label("count")
            ).group_by(MovimentacaoBancaria.categoria).all()
            
            if categorias:
                st.write("### Distribuição por Categorias")
                
                categorias_df = pd.DataFrame([(c.categoria, c.count) for c in categorias], 
                                           columns=["Categoria", "Quantidade"])
                
                st.dataframe(categorias_df, use_container_width=True)
        
        # Botão para limpar dados
        if plano_contas_count > 0 or movimentacoes_count > 0:
            if st.button("Limpar Todos os Dados Importados", type="secondary"):
                if st.checkbox("Confirmo que desejo excluir todos os dados importados"):
                    with st.spinner("Excluindo dados..."):
                        db.query(MovimentacaoBancaria).delete()
                        db.query(PlanoContas).delete()
                        db.commit()
                        st.success("✅ Todos os dados foram excluídos com sucesso!")
                        st.experimental_rerun()
    
    except Exception as e:
        st.error(f"❌ Erro ao consultar o banco de dados: {str(e)}")
    finally:
        db.close()
    
    # Exibe instruções de navegação
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Ver Dashboard Otimizado"):
            st.switch_page("pages/dashboard_financeiro_otimizado.py")
    
    with col2:
        if st.button("Voltar para o Menu Principal"):
            st.switch_page("main.py")

if __name__ == "__main__":
    main()