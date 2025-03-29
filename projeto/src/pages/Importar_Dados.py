import streamlit as st
import pandas as pd
import sys
import os
import tempfile
import re
from datetime import datetime
from io import StringIO

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, test_connection
from models import MovimentacaoBancaria, PlanoContas

def converter_data(data_str):
    """Converte string de data para objeto datetime"""
    if pd.isna(data_str) or data_str == '':
        return None
    
    formatos = [
        '%d/%m/%Y',  # 31/12/2023
        '%d-%m-%Y',  # 31-12-2023
        '%Y-%m-%d',  # 2023-12-31
        '%d.%m.%Y',  # 31.12.2023
        '%m/%d/%Y',  # 12/31/2023
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(data_str, formato).date()
        except:
            continue
    
    return None

def limpar_valor_monetario(valor_str):
    """Converte string de valor monetário para float"""
    if pd.isna(valor_str) or valor_str == '':
        return 0.0
    
    # Remove caracteres não numéricos, exceto ponto e vírgula
    if isinstance(valor_str, str):
        # Substitui vírgula por ponto
        valor_str = valor_str.replace(',', '.')
        # Remove caracteres não numéricos
        valor_str = re.sub(r'[^\d.]', '', valor_str)
        try:
            return float(valor_str)
        except:
            return 0.0
    elif isinstance(valor_str, (int, float)):
        return float(valor_str)
    else:
        return 0.0

def categorizar_natureza(codigo, nome):
    """Categoriza a natureza em grupos contábeis principais"""
    if pd.isna(codigo) or codigo == '':
        return 'Não categorizado'
    
    # Categorias simplificadas baseadas no nome da natureza
    nome_lower = str(nome).lower() if not pd.isna(nome) else ''
    
    # Categorias de Receitas
    if any(termo in nome_lower for termo in ['receita', 'venda', 'faturamento', 'entrada']):
        return 'Receitas Operacionais'
    
    # Categorias de Custos
    if any(termo in nome_lower for termo in ['custo', 'produto', 'materia']):
        return 'Custos dos Serviços'
    
    # Categorias de Despesas
    if any(termo in nome_lower for termo in ['despesa', 'administrativ', 'escritorio']):
        return 'Despesas Administrativas'
    
    if any(termo in nome_lower for termo in ['salario', 'folha', 'pessoal']):
        return 'Despesas com Pessoal'
    
    if any(termo in nome_lower for termo in ['marketing', 'propaganda', 'publicidade']):
        return 'Despesas com Marketing'
    
    if any(termo in nome_lower for termo in ['imposto', 'tributo', 'taxa', 'fiscal']):
        return 'Impostos e Taxas'
    
    # Outras categorias
    if any(termo in nome_lower for termo in ['transferencia', 'aplicacao', 'investimento']):
        return 'Movimentações Financeiras'
    
    # Se não identificou, tenta usar o primeiro dígito do código
    codigo_str = str(codigo).strip().replace('.0', '')
    if codigo_str:
        primeiro_digito = codigo_str[0]
        if primeiro_digito == '1':
            return 'Ativo'
        elif primeiro_digito == '2':
            return 'Passivo'
        elif primeiro_digito == '3':
            return 'Receitas'
        elif primeiro_digito == '4':
            return 'Despesas'
    
    return 'Outros'

def is_custo_fixo(categoria, historico):
    """Determina se um lançamento é custo fixo com base na categoria e histórico"""
    categoria_lower = str(categoria).lower()
    historico_lower = str(historico).lower() if not pd.isna(historico) else ''
    
    # Lista de termos que indicam custos fixos
    termos_fixos = [
        'aluguel', 'condomínio', 'iptu', 'luz', 'energia', 'água', 
        'telefone', 'internet', 'assinatura', 'mensalidade',
        'salário', 'folha', 'pro-labore', 'honorários'
    ]
    
    return any(termo in categoria_lower or termo in historico_lower for termo in termos_fixos)

def importar_plano_contas(df):
    """Importa o plano de contas do DataFrame para o banco de dados"""
    try:
        # Seleciona apenas as colunas relevantes para o plano de contas
        if 'Natureza' in df.columns and 'Nome Natureza' in df.columns:
            plano_df = df[['Natureza', 'Nome Natureza']].drop_duplicates().dropna(subset=['Natureza'])
            
            # Processa códigos
            plano_df['Natureza'] = plano_df['Natureza'].astype(str).str.replace('.0', '')
            
            # Adiciona categorização
            plano_df['Categoria'] = plano_df.apply(
                lambda row: categorizar_natureza(row['Natureza'], row['Nome Natureza']), 
                axis=1
            )
            
            # Cria um dicionário para armazenar códigos e descrições
            codigos_plano = {}
            
            # Adiciona códigos do plano de contas ao dicionário
            for _, row in plano_df.iterrows():
                if pd.notna(row['Natureza']) and pd.notna(row['Nome Natureza']):
                    codigos_plano[row['Natureza']] = {
                        'descricao': row['Nome Natureza'],
                        'categoria': row['Categoria']
                    }
            
            # Limpa as tabelas - IMPORTANTE: primeiro movimentações, depois plano de contas
            db = get_db()
            db.query(MovimentacaoBancaria).delete()  # Primeiro limpa movimentações
            db.query(PlanoContas).delete()           # Depois limpa plano de contas
            
            # Insere todos os registros do dicionário
            for codigo, dados in codigos_plano.items():
                conta = PlanoContas(
                    codigo=codigo,
                    descricao=dados['descricao'],
                    categoria=dados['categoria']
                )
                db.add(conta)
            
            db.commit()
            return True, f"Importados {len(codigos_plano)} registros do plano de contas com sucesso!"
        else:
            return False, "Arquivo CSV não contém as colunas necessárias (Natureza, Nome Natureza)"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return False, f"Erro ao importar plano de contas: {str(e)}"
    
    finally:
        if 'db' in locals():
            db.close()

def importar_movimentacoes(df):
    """Importa as movimentações bancárias do DataFrame para o banco de dados"""
    try:
        # Converte tipos de dados
        df['Data'] = df['Data'].apply(converter_data)
        df['Entrada'] = df['Entrada'].apply(limpar_valor_monetario)
        df['Saida'] = df['Saida'].apply(limpar_valor_monetario)
        
        # Converte códigos para string
        for col in ['Agencia', 'Conta Banco', 'Natureza']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.0', '')
                df[col] = df[col].replace('nan', '')
        
        # Remove linhas com datas inválidas ou nulas
        df = df.dropna(subset=['Data'])
        
        # Adiciona informações extras
        df['Categoria'] = df.apply(
            lambda row: categorizar_natureza(row['Natureza'], row['Nome Natureza']), 
            axis=1
        )
        
        df['Tipo'] = df.apply(
            lambda row: 'Fixo' if is_custo_fixo(row['Nome Natureza'], row['Historico']) else 'Variável', 
            axis=1
        )
        
        # Limpa a tabela de movimentações
        db = get_db()
        db.query(MovimentacaoBancaria).delete()
        
        # Adiciona os registros em lotes
        registros = []
        count = 0
        
        for _, row in df.iterrows():
            try:
                # Verifica se é uma linha válida com data
                if pd.isna(row['Data']):
                    continue
                
                # Padrão para uma filial única
                filial = "1"  # Filial única
                
                mov = MovimentacaoBancaria(
                    filial=filial,
                    data=row['Data'],
                    banco=str(row['Banco']),
                    agencia=str(row['Agencia']),
                    conta=str(row['Conta Banco']),
                    natureza=str(row['Natureza']),
                    nome_natureza=str(row['Nome Natureza']),
                    documento=str(row['Documento']),
                    entrada=row['Entrada'] if not pd.isna(row['Entrada']) else None,
                    saida=row['Saida'] if not pd.isna(row['Saida']) else None,
                    historico=str(row['Historico']),
                    categoria=str(row.get('Categoria', 'Não categorizado')),
                    tipo_custo=str(row.get('Tipo', 'Não classificado'))
                )
                registros.append(mov)
                count += 1
                
                # Commit a cada 50 registros
                if len(registros) >= 50:
                    db.add_all(registros)
                    db.commit()
                    registros = []
            except Exception as e:
                print(f"Erro ao processar linha {_}: {e}")
                continue  # Pula para a próxima linha em caso de erro
        
        # Adiciona registros restantes
        if registros:
            db.add_all(registros)
            db.commit()
            
        return True, f"Importados {count} registros de movimentações bancárias"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return False, f"Erro ao importar movimentações: {str(e)}"
    
    finally:
        if 'db' in locals():
            db.close()

def main():
    st.title("Importação de Dados")
    
    # Verifica a conexão com o banco
    with st.spinner("Verificando conexão com o banco de dados..."):
        connection_result = test_connection()
    
    if not connection_result:
        st.error("❌ Não foi possível conectar ao banco de dados!")
        
        if st.button("Verificar Status do Banco"):
            st.switch_page("pages/db_status.py")
        
        return
    
    st.write("""
    ### Importação de Dados Contábeis
    
    Importe dados de movimentações bancárias a partir de um arquivo CSV.
    O arquivo deve conter as seguintes colunas:
    
    - **Data**: Data da movimentação
    - **Banco**: Nome ou código do banco
    - **Natureza**: Código da natureza contábil
    - **Nome Natureza**: Descrição da natureza contábil
    - **Entrada**: Valores recebidos
    - **Saida**: Valores pagos
    - **Historico**: Descrição da movimentação
    """)
    
    uploaded_file = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Lê o arquivo
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                # Tenta com encoding diferente se falhar
                df = pd.read_csv(uploaded_file, encoding='latin1')
            
            # Exibe prévia
            st.subheader("Prévia dos Dados")
            st.dataframe(df.head(5))
            
            # Verifica colunas obrigatórias
            required_columns = ['Data', 'Banco', 'Natureza', 'Nome Natureza', 'Entrada', 'Saida', 'Historico']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
            else:
                # Botões para importar
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Limpar Dados Existentes e Importar", type="primary"):
                        with st.spinner("Importando dados..."):
                            # Primeiro importa o plano de contas
                            success_plano, message_plano = importar_plano_contas(df)
                            
                            if success_plano:
                                # Se plano foi importado com sucesso, importa as movimentações
                                success_mov, message_mov = importar_movimentacoes(df)
                                
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
                
                with col2:
                    if st.button("Cancelar"):
                        st.experimental_rerun()
                        
                # Estatísticas do arquivo
                if 'Data' in df.columns:
                    st.subheader("Estatísticas do Arquivo")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total de Registros", f"{len(df):,}")
                    
                    with col2:
                        entradas = df['Entrada'].apply(limpar_valor_monetario).sum()
                        st.metric("Total de Entradas", f"R$ {entradas:,.2f}")
                    
                    with col3:
                        saidas = df['Saida'].apply(limpar_valor_monetario).sum()
                        st.metric("Total de Saídas", f"R$ {saidas:,.2f}")
        
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
            
            # Botão para ver dashboard
            if st.button("Ver Dashboard Financeiro", type="primary"):
                st.switch_page("pages/dashboard_financeiro.py")
            
        elif plano_contas_count > 0 or movimentacoes_count > 0:
            # Aviso de dados inconsistentes
            st.warning("⚠️ Dados podem estar inconsistentes. Considere reimportar os dados.")
        else:
            # Não há dados
            st.info("ℹ️ Não há dados importados no sistema. Por favor, importe um arquivo CSV.")
            
            # Exibe exemplo
            with st.expander("Ver exemplo de formato de arquivo CSV"):
                st.write("""
                ```
                Data,Banco,Agencia,Conta Banco,Natureza,Nome Natureza,Documento,Entrada,Saida,Historico
                01/01/2023,Banco X,1234,56789,1001,Receita de Vendas,NF-001,5000.00,0.00,Faturamento Cliente ABC
                15/01/2023,Banco X,1234,56789,2001,Aluguel,BOL-123,0.00,1500.00,Pagamento aluguel sede
                ```
                """)
    except Exception as e:
        st.error(f"❌ Erro ao consultar o banco de dados: {str(e)}")
    finally:
        db.close()
    
    # Botões no rodapé
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Verificar Status do Banco"):
            st.switch_page("pages/Diagnostico_do_Banco_de_Dados.py")
    
    with col2:
        if st.button("Voltar para o Menu Principal"):
            st.switch_page("main.py")

if __name__ == "__main__":
    main()