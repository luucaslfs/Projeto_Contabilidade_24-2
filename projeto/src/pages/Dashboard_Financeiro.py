import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import sys
import os
from dateutil.relativedelta import relativedelta

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, test_connection
from models import Despesa, Fatura, MovimentacaoBancaria, PlanoContas

def load_data():
    """Carrega todos os dados necessários para o dashboard"""
    db = get_db()
    try:
        # Carrega despesas
        despesas = db.query(Despesa).all()
        
        # Carrega faturas
        faturas = db.query(Fatura).all()
        
        # Carrega movimentações bancárias
        movimentacoes = db.query(MovimentacaoBancaria).all()
        
        # Carrega plano de contas
        plano_contas = db.query(PlanoContas).all()
        
        return {
            'despesas': despesas,
            'faturas': faturas,
            'movimentacoes': movimentacoes,
            'plano_contas': plano_contas
        }
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None
    finally:
        db.close()

def get_month_name(month_number):
    """Retorna o nome do mês em português"""
    months = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    return months.get(month_number, '')

def create_movimentacoes_df(movimentacoes):
    """Cria DataFrame para análise de movimentações"""
    if not movimentacoes:
        return pd.DataFrame()
        
    data = []
    for m in movimentacoes:
        data.append({
            'data': m.data,
            'mes': m.data.month,
            'ano': m.data.year,
            'mes_ano': f"{get_month_name(m.data.month)}/{m.data.year}",
            'natureza': m.natureza,
            'nome_natureza': m.nome_natureza if hasattr(m, 'nome_natureza') else '',
            'categoria': m.categoria if hasattr(m, 'categoria') else '',
            'tipo_custo': m.tipo_custo if hasattr(m, 'tipo_custo') else 'Não classificado',
            'entrada': m.entrada if m.entrada else 0,
            'saida': m.saida if m.saida else 0,
            'valor_liquido': (m.entrada if m.entrada else 0) - (m.saida if m.saida else 0),
            'historico': m.historico
        })
    return pd.DataFrame(data)

def create_despesas_df(despesas):
    """Cria DataFrame para análise de despesas"""
    if not despesas:
        return pd.DataFrame()
        
    data = []
    for d in despesas:
        if hasattr(d, 'data_despesa') and d.data_despesa:
            data.append({
                'data': d.data_despesa,
                'mes': d.data_despesa.month,
                'ano': d.data_despesa.year,
                'mes_ano': f"{get_month_name(d.data_despesa.month)}/{d.data_despesa.year}",
                'descricao': d.descricao,
                'categoria': d.categoria,
                'tipo': d.tipo if hasattr(d, 'tipo') else 'Variável',
                'valor': d.valor
            })
    return pd.DataFrame(data)

def create_faturas_df(faturas):
    """Cria DataFrame para análise de faturas"""
    if not faturas:
        return pd.DataFrame()
        
    data = []
    for f in faturas:
        try:
            if hasattr(f, 'mes_referencia') and f.mes_referencia:
                data.append({
                    'data_emissao': f.data_emissao,
                    'mes_referencia': f.mes_referencia,
                    'mes': f.mes_referencia.month,
                    'ano': f.mes_referencia.year,
                    'mes_ano': f"{get_month_name(f.mes_referencia.month)}/{f.mes_referencia.year}",
                    'valor': f.valor,
                    'status': f.status
                })
        except Exception as e:
            print(f"Erro ao processar fatura {f.id if hasattr(f, 'id') else 'desconhecido'}: {e}")
    return pd.DataFrame(data)

def calcular_custos_fixos_variaveis(df_movimentacoes):
    """Calcula custos fixos e variáveis"""
    # Verifica se há dados suficientes
    if df_movimentacoes.empty or 'saida' not in df_movimentacoes.columns:
        return pd.DataFrame(columns=['tipo_custo', 'saida'])
    
    # Filtra apenas as saídas
    df_custos = df_movimentacoes[df_movimentacoes['saida'] > 0].copy()
    
    # Verifica se há saídas
    if df_custos.empty:
        return pd.DataFrame(columns=['tipo_custo', 'saida'])
    
    # Verifica se tem a coluna tipo_custo
    if 'tipo_custo' not in df_custos.columns:
        df_custos['tipo_custo'] = 'Não classificado'
    
    # Agrega por tipo de custo
    custos_tipo = df_custos.groupby('tipo_custo')['saida'].sum().reset_index()
    
    # Se não houver classificação, cria uma básica
    if len(custos_tipo) == 1 and custos_tipo.iloc[0]['tipo_custo'] == 'Não classificado':
        # Verifica se tem a coluna historico
        if 'historico' in df_custos.columns:
            # Identifica custos fixos comuns
            termos_fixos = ['aluguel', 'salário', 'salario', 'folha', 'condomínio', 'condominio', 
                            'internet', 'telefone', 'água', 'agua', 'luz', 'energia']
            
            # Classifica com base no histórico
            df_custos['tipo_custo'] = df_custos['historico'].apply(
                lambda x: 'Fixo' if any(termo in str(x).lower() for termo in termos_fixos) else 'Variável'
            )
            
            # Reagrupa
            custos_tipo = df_custos.groupby('tipo_custo')['saida'].sum().reset_index()
    
    return custos_tipo

def calcular_metricas(df_movimentacoes, df_despesas, df_faturas, periodo_inicio, periodo_fim):
    """Calcula as principais métricas financeiras para o período selecionado"""
    # Verifica se os DataFrames têm as colunas necessárias
    mov_periodo = pd.DataFrame()
    despesas_periodo = pd.DataFrame()
    faturas_periodo = pd.DataFrame()
    
    # Filtra movimentações pelo período
    if not df_movimentacoes.empty and 'data' in df_movimentacoes.columns:
        mov_periodo = df_movimentacoes[(df_movimentacoes['data'] >= periodo_inicio) & 
                                      (df_movimentacoes['data'] <= periodo_fim)]
    else:
        mov_periodo = df_movimentacoes.copy()
    
    # Filtra despesas pelo período
    if not df_despesas.empty and 'data' in df_despesas.columns:
        despesas_periodo = df_despesas[(df_despesas['data'] >= periodo_inicio) & 
                                      (df_despesas['data'] <= periodo_fim)]
    else:
        despesas_periodo = df_despesas.copy()
    
    # Filtra faturas pelo período
    if not df_faturas.empty and 'mes_referencia' in df_faturas.columns:
        faturas_periodo = df_faturas[(df_faturas['mes_referencia'] >= periodo_inicio) & 
                                    (df_faturas['mes_referencia'] <= periodo_fim)]
    else:
        faturas_periodo = df_faturas.copy()
    
    # Cálculo das métricas
    total_receitas = 0
    total_despesas = 0
    
    if 'entrada' in mov_periodo.columns:
        total_receitas = mov_periodo['entrada'].sum()
    
    if 'saida' in mov_periodo.columns:
        total_despesas = mov_periodo['saida'].sum()
    
    # Custos fixos e variáveis
    custos_tipo = calcular_custos_fixos_variaveis(mov_periodo)
    custos_fixos = 0
    custos_variaveis = 0
    
    if not custos_tipo.empty:
        custos_fixos = custos_tipo[custos_tipo['tipo_custo'] == 'Fixo']['saida'].sum() if 'Fixo' in custos_tipo['tipo_custo'].values else 0
        custos_variaveis = custos_tipo[custos_tipo['tipo_custo'] == 'Variável']['saida'].sum() if 'Variável' in custos_tipo['tipo_custo'].values else 0
    
    # Categorias de despesas
    despesas_por_categoria = pd.DataFrame(columns=['categoria', 'valor'])
    
    if not despesas_periodo.empty and 'categoria' in despesas_periodo.columns and 'valor' in despesas_periodo.columns:
        despesas_por_categoria = despesas_periodo.groupby('categoria')['valor'].sum().reset_index()
    elif not mov_periodo.empty and 'saida' in mov_periodo.columns and 'categoria' in mov_periodo.columns:
        # Se não houver despesas registradas, tenta usar as movimentações
        df_saidas = mov_periodo[mov_periodo['saida'] > 0].copy()
        if not df_saidas.empty:
            despesas_por_categoria = df_saidas.groupby('categoria')['saida'].sum().reset_index()
            despesas_por_categoria.rename(columns={'saida': 'valor'}, inplace=True)
    
    # Faturamento mensal
    faturamento_mensal = pd.DataFrame(columns=['ano', 'mes', 'mes_ano', 'valor'])
    
    if not faturas_periodo.empty and 'valor' in faturas_periodo.columns:
        if 'ano' in faturas_periodo.columns and 'mes' in faturas_periodo.columns and 'mes_ano' in faturas_periodo.columns:
            faturamento_mensal = faturas_periodo.groupby(['ano', 'mes', 'mes_ano'])['valor'].sum().reset_index()
            faturamento_mensal = faturamento_mensal.sort_values(by=['ano', 'mes'])
    elif not mov_periodo.empty and 'entrada' in mov_periodo.columns:
        # Se não houver faturas, tenta usar as entradas de movimentações
        entradas = mov_periodo[mov_periodo['entrada'] > 0]
        if not entradas.empty and 'ano' in entradas.columns and 'mes' in entradas.columns and 'mes_ano' in entradas.columns:
            faturamento_mensal = entradas.groupby(['ano', 'mes', 'mes_ano'])['entrada'].sum().reset_index()
            faturamento_mensal.rename(columns={'entrada': 'valor'}, inplace=True)
            faturamento_mensal = faturamento_mensal.sort_values(by=['ano', 'mes'])
    
    # Receitas vs Despesas por mês
    receitas_despesas_mes = pd.DataFrame(columns=['ano', 'mes', 'mes_ano', 'entrada', 'saida', 'valor_liquido'])
    
    if not mov_periodo.empty and 'ano' in mov_periodo.columns and 'mes' in mov_periodo.columns and 'mes_ano' in mov_periodo.columns:
        if 'entrada' in mov_periodo.columns and 'saida' in mov_periodo.columns and 'valor_liquido' in mov_periodo.columns:
            receitas_despesas_mes = mov_periodo.groupby(['ano', 'mes', 'mes_ano']).agg({
                'entrada': 'sum',
                'saida': 'sum',
                'valor_liquido': 'sum'
            }).reset_index()
            receitas_despesas_mes = receitas_despesas_mes.sort_values(by=['ano', 'mes'])
    
    # KPIs
    margem_lucro = 0 if total_receitas == 0 else (total_receitas - total_despesas) / total_receitas * 100
    
    # Índice de fixação de despesas (Martins, 2018)
    indice_fixacao = 0 if total_despesas == 0 else (custos_fixos / total_despesas) * 100
    
    return {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'custos_fixos': custos_fixos,
        'custos_variaveis': custos_variaveis,
        'indice_fixacao': indice_fixacao,
        'saldo': total_receitas - total_despesas,
        'margem_lucro': margem_lucro,
        'despesas_por_categoria': despesas_por_categoria,
        'faturamento_mensal': faturamento_mensal,
        'receitas_despesas_mes': receitas_despesas_mes
    }

def plot_receitas_despesas(receitas_despesas_mes):
    """Gráfico de Receitas vs Despesas por mês"""
    # Verifica se há dados para plotar
    if receitas_despesas_mes.empty or 'mes_ano' not in receitas_despesas_mes.columns:
        return None
        
    fig = go.Figure()
    
    if 'entrada' in receitas_despesas_mes.columns:
        fig.add_trace(go.Bar(
            x=receitas_despesas_mes['mes_ano'],
            y=receitas_despesas_mes['entrada'],
            name='Receitas',
            marker_color='#2E8B57'  # Verde
        ))
    
    if 'saida' in receitas_despesas_mes.columns:
        fig.add_trace(go.Bar(
            x=receitas_despesas_mes['mes_ano'],
            y=receitas_despesas_mes['saida'],
            name='Despesas',
            marker_color='#CD5C5C'  # Vermelho
        ))
    
    if 'valor_liquido' in receitas_despesas_mes.columns:
        fig.add_trace(go.Scatter(
            x=receitas_despesas_mes['mes_ano'],
            y=receitas_despesas_mes['valor_liquido'],
            name='Saldo',
            mode='lines+markers',
            line=dict(color='#4682B4', width=3)  # Azul
        ))
    
    fig.update_layout(
        title='Receitas vs Despesas por Mês',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_despesas_categoria(despesas_por_categoria):
    """Gráfico de Despesas por Categoria"""
    if despesas_por_categoria.empty or 'categoria' not in despesas_por_categoria.columns or 'valor' not in despesas_por_categoria.columns:
        return None
        
    fig = px.pie(
        despesas_por_categoria, 
        values='valor', 
        names='categoria',
        title='Distribuição de Despesas por Categoria',
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def plot_custos_fixos_variaveis(custos_fixos, custos_variaveis):
    """Gráfico de distribuição de custos fixos vs variáveis"""
    # Verifica se há valores para plotar
    if custos_fixos == 0 and custos_variaveis == 0:
        return None
        
    labels = ['Custos Fixos', 'Custos Variáveis']
    values = [custos_fixos, custos_variaveis]
    
    fig = px.pie(
        values=values,
        names=labels,
        title='Custos Fixos vs Variáveis (Martins, 2018)',
        color_discrete_sequence=['#1E88E5', '#FFC107']
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

def plot_faturamento_mensal(faturamento_mensal):
    """Gráfico de Faturamento Mensal"""
    if faturamento_mensal.empty or 'mes_ano' not in faturamento_mensal.columns or 'valor' not in faturamento_mensal.columns:
        return None
        
    fig = px.line(
        faturamento_mensal,
        x='mes_ano',
        y='valor',
        title='Faturamento Mensal',
        markers=True
    )
    
    fig.update_layout(
        xaxis_title='Mês/Ano',
        yaxis_title='Valor Faturado (R$)',
        xaxis_tickangle=-45
    )
    
    return fig

def plot_analise_vertical(df_movimentacoes, periodo_inicio, periodo_fim):
    """Cria gráfico de análise vertical conforme Pereira da Silva (2017)"""
    # Verifica se há dados para análise
    if df_movimentacoes.empty or 'data' not in df_movimentacoes.columns:
        return None
        
    # Filtra os dados pelo período
    mov_periodo = df_movimentacoes[(df_movimentacoes['data'] >= periodo_inicio) & 
                                   (df_movimentacoes['data'] <= periodo_fim)]
    
    # Verifica se tem dados após o filtro
    if mov_periodo.empty:
        return None
    
    # Verifica se tem as colunas necessárias
    if 'entrada' not in mov_periodo.columns or 'saida' not in mov_periodo.columns:
        return None
    
    # Separa entradas e saídas
    entradas = mov_periodo[mov_periodo['entrada'] > 0]
    saidas = mov_periodo[mov_periodo['saida'] > 0]
    
    # Verifica se tem saídas para analisar
    if saidas.empty:
        return None
    
    # Calcula o total de entradas e saídas
    total_entradas = entradas['entrada'].sum()
    total_saidas = saidas['saida'].sum()
    
    # Prepara dados para o gráfico de análise vertical de despesas
    if 'categoria' in saidas.columns:
        # Agrupa saídas por categoria
        despesas_categoria = saidas.groupby('categoria')['saida'].sum().reset_index()
        
        # Calcula o percentual sobre o total
        despesas_categoria['percentual'] = (despesas_categoria['saida'] / total_saidas * 100).round(1)
        
        # Ordena por valor (decrescente)
        despesas_categoria = despesas_categoria.sort_values(by='saida', ascending=False)
        
        # Cria o gráfico de barras
        fig = px.bar(
            despesas_categoria,
            x='categoria',
            y='percentual',
            text='percentual',
            title='Análise Vertical de Despesas (Pereira da Silva, 2017)',
            color='saida',
            color_continuous_scale=px.colors.sequential.Reds
        )
        
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        
        fig.update_layout(
            xaxis_title='Categoria',
            yaxis_title='% do Total de Despesas',
            xaxis_tickangle=-45,
            yaxis=dict(range=[0, max(despesas_categoria['percentual']) * 1.1])
        )
        
        return fig
    
    return None

def main():
    st.title("Dashboard Financeiro - Agência de Publicidade")
    
    # Adiciona um diagnóstico da conexão com o banco
    with st.spinner("Verificando conexão com o banco de dados..."):
        connection_result = test_connection()
    
    if not connection_result:
        st.error("❌ Não foi possível conectar ao banco de dados!")
        st.info("Por favor, acesse a página de status do banco para diagnóstico ou importe dados primeiro.")
        if st.button("Verificar Status do Banco"):
            st.switch_page("pages/Diagnostico_do_Banco_de_Dados.py")
        if st.button("Importar Dados"):
            st.switch_page("pages/Importar_Dados.py")
        return
    
    # Carrega os dados
    with st.spinner("Carregando dados..."):
        data = load_data()
    
    if not data:
        st.error("❌ Não foi possível carregar os dados!")
        return
    
    # Extrai os dados carregados
    despesas = data['despesas']
    faturas = data['faturas']
    movimentacoes = data['movimentacoes']
    
    # Cria DataFrames para análise
    df_movimentacoes = create_movimentacoes_df(movimentacoes)
    df_despesas = create_despesas_df(despesas)
    df_faturas = create_faturas_df(faturas)
    
    # Se não houver dados, exibe mensagem
    if df_movimentacoes.empty and df_despesas.empty and df_faturas.empty:
        st.warning("⚠️ Não há dados suficientes para gerar o dashboard. Por favor, importe ou cadastre dados.")
        
        # Botão para importar dados
        if st.button("Ir para Importação de Dados"):
            st.switch_page("pages/importacao_dados.py")
        
        return
    
    # Define data mín/máx para o filtro de período
    data_min = datetime.now().date() - timedelta(days=180)  # Padrão: 6 meses atrás
    data_max = datetime.now().date()  # Padrão: hoje
    
    # Tenta obter datas dos dados
    if not df_movimentacoes.empty and 'data' in df_movimentacoes.columns:
        data_min = df_movimentacoes['data'].min()
        data_max = df_movimentacoes['data'].max()
    elif not df_despesas.empty and 'data' in df_despesas.columns:
        data_min = df_despesas['data'].min()
        data_max = df_despesas['data'].max()
    elif not df_faturas.empty and 'mes_referencia' in df_faturas.columns:
        data_min = df_faturas['mes_referencia'].min()
        data_max = df_faturas['mes_referencia'].max()
    
    # Filtros de período na barra lateral
    st.sidebar.subheader("Filtros")
    periodo_inicio = st.sidebar.date_input("Data Início", value=data_min)
    periodo_fim = st.sidebar.date_input("Data Fim", value=data_max)
    
    # Verifica se as datas são válidas
    if periodo_inicio > periodo_fim:
        st.error("❌ Data de início não pode ser posterior à data de fim!")
        return
    
    # Calcula as métricas
    with st.spinner("Calculando métricas..."):
        metricas = calcular_metricas(df_movimentacoes, df_despesas, df_faturas, periodo_inicio, periodo_fim)
    
    # Tabs para organizar o dashboard
    tab1, tab2, tab3 = st.tabs([
        "Visão Geral", 
        "Análise de Custos",
        "Análise Temporal"
    ])
    
    with tab1:
        st.subheader("Indicadores Financeiros")
        
        # KPIs principais - linha 1
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Receitas Totais",
                value=f"R$ {metricas['total_receitas']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Despesas Totais",
                value=f"R$ {metricas['total_despesas']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Resultado do Período",
                value=f"R$ {metricas['saldo']:,.2f}",
                delta=f"{metricas['margem_lucro']:.2f}%" if metricas['margem_lucro'] != 0 else None,
                delta_color="normal"
            )
        
        # Gráfico principal - Receitas vs Despesas
        st.subheader("Evolução Mensal de Receitas e Despesas")
        
        if not metricas['receitas_despesas_mes'].empty:
            fig_receitas_despesas = plot_receitas_despesas(metricas['receitas_despesas_mes'])
            if fig_receitas_despesas:
                st.plotly_chart(fig_receitas_despesas, use_container_width=True)
                
                st.info("""
                **Análise Temporal (Pereira da Silva, 2017)**: Este gráfico demonstra a evolução 
                mensal das receitas e despesas, permitindo identificar tendências e sazonalidades.
                """)
            else:
                st.info("ℹ️ Não há dados suficientes para gerar o gráfico de evolução mensal.")
        else:
            st.info("ℹ️ Não há dados suficientes para gerar o gráfico de evolução mensal.")
        
        # Distribuição de despesas por categoria
        st.subheader("Análise de Despesas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not metricas['despesas_por_categoria'].empty:
                fig_categorias = plot_despesas_categoria(metricas['despesas_por_categoria'])
                if fig_categorias:
                    st.plotly_chart(fig_categorias, use_container_width=True)
                else:
                    st.info("ℹ️ Não há dados suficientes para gerar o gráfico de despesas por categoria.")
            else:
                st.info("ℹ️ Não há dados de despesas categorizadas para o período selecionado.")
        
        with col2:
            # Análise Vertical
            fig_analise_vertical = plot_analise_vertical(df_movimentacoes, periodo_inicio, periodo_fim)
            if fig_analise_vertical:
                st.plotly_chart(fig_analise_vertical, use_container_width=True)
            else:
                st.info("ℹ️ Não há dados suficientes para gerar a análise vertical.")
    
    with tab2:
        st.subheader("Análise de Custos (Martins, 2018)")
        
        # KPIs de custos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Custos Fixos",
                value=f"R$ {metricas['custos_fixos']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Custos Variáveis",
                value=f"R$ {metricas['custos_variaveis']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Índice de Fixação de Despesas",
                value=f"{metricas['indice_fixacao']:.2f}%",
                help="% dos custos que são fixos (independem do volume de serviços)"
            )
        
        # Gráfico de custos fixos vs variáveis
        col1, col2 = st.columns(2)
        
        with col1:
            fig_custos = plot_custos_fixos_variaveis(metricas['custos_fixos'], metricas['custos_variaveis'])
            if fig_custos:
                st.plotly_chart(fig_custos, use_container_width=True)
            else:
                st.info("ℹ️ Não há dados suficientes para gerar o gráfico de custos fixos vs variáveis.")
        
        with col2:
            st.write("### Interpretação dos Custos")
            st.info("""
            **Segundo Martins (2018)**, os custos fixos são aqueles que não variam com o volume 
            de produção ou serviços prestados, como aluguel e salários administrativos.
            
            Já os custos variáveis são diretamente proporcionais ao volume, como comissões 
            e materiais consumidos.
            
            O **Índice de Fixação de Despesas** indica a rigidez da estrutura de custos:
            - Valores acima de 70%: estrutura rígida, maior risco operacional
            - Valores abaixo de 30%: estrutura flexível, menor risco
            """)
            
            # Interpreta o índice de fixação
            indice = metricas['indice_fixacao']
            if indice > 70:
                st.warning(f"**Índice de Fixação: {indice:.1f}%** - A agência possui uma estrutura de custos **rígida**, com alta proporção de custos fixos. Isso representa maior risco em períodos de baixa receita.")
            elif indice < 30:
                st.success(f"**Índice de Fixação: {indice:.1f}%** - A agência possui uma estrutura de custos **flexível**, com baixa proporção de custos fixos. Isso representa menor risco em períodos de baixa receita.")
            else:
                st.info(f"**Índice de Fixação: {indice:.1f}%** - A agência possui uma estrutura de custos **moderada**, com equilíbrio entre custos fixos e variáveis.")
                
        # Ponto de Equilíbrio (conceito de Martins)
        st.subheader("Ponto de Equilíbrio")
        
        # Calcula o ponto de equilíbrio
        if metricas['total_receitas'] > 0 and metricas['custos_variaveis'] < metricas['total_receitas']:
            # Calcula margem de contribuição
            margem_contribuicao = metricas['total_receitas'] - metricas['custos_variaveis']
            indice_mc = margem_contribuicao / metricas['total_receitas']
            
            # Ponto de equilíbrio
            pe = metricas['custos_fixos'] / indice_mc if indice_mc > 0 else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="Ponto de Equilíbrio",
                    value=f"R$ {pe:,.2f}",
                    help="Receita necessária para cobrir todos os custos"
                )
                
                # Verifica se está acima do ponto de equilíbrio
                if metricas['total_receitas'] > pe:
                    folga = metricas['total_receitas'] - pe
                    st.success(f"A agência está **acima** do ponto de equilíbrio, com folga de R$ {folga:,.2f}")
                else:
                    deficit = pe - metricas['total_receitas']
                    st.error(f"A agência está **abaixo** do ponto de equilíbrio, com déficit de R$ {deficit:,.2f}")
            
            with col2:
                st.info("""
                **Ponto de Equilíbrio (Martins, 2018)**: É o valor de receita necessário para 
                cobrir exatamente todos os custos, sem gerar lucro ou prejuízo.
                
                PE = Custos Fixos ÷ Índice de Margem de Contribuição
                
                O Índice de Margem de Contribuição é calculado como:
                (Receita - Custos Variáveis) ÷ Receita
                """)
        else:
            st.warning("Não foi possível calcular o ponto de equilíbrio. É necessário ter receitas positivas e custos variáveis menores que as receitas.")
    
    with tab3:
        st.subheader("Análise Temporal (Pereira da Silva, 2017)")
        
        # Gráfico de Faturamento Mensal
        st.write("### Evolução do Faturamento")
        
        if not metricas['faturamento_mensal'].empty:
            fig_faturamento = plot_faturamento_mensal(metricas['faturamento_mensal'])
            if fig_faturamento:
                st.plotly_chart(fig_faturamento, use_container_width=True)
                
                # Cálculo de tendência
                if len(metricas['faturamento_mensal']) >= 3:
                    valores = metricas['faturamento_mensal']['valor'].tolist()
                    primeiro_valor = valores[0]
                    ultimo_valor = valores[-1]
                    
                    variacao_percentual = ((ultimo_valor / primeiro_valor) - 1) * 100 if primeiro_valor > 0 else 0
                    
                    st.write("### Análise de Tendência")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            label="Variação no Período",
                            value=f"{variacao_percentual:.2f}%",
                            delta=None
                        )
                    
                    with col2:
                        # Análise da tendência
                        if variacao_percentual > 10:
                            st.success("**Tendência de CRESCIMENTO** no faturamento ao longo do período analisado.")
                        elif variacao_percentual < -10:
                            st.error("**Tendência de QUEDA** no faturamento ao longo do período analisado.")
                        else:
                            st.info("**Tendência de ESTABILIDADE** no faturamento ao longo do período analisado.")
            else:
                st.info("ℹ️ Não há dados suficientes para gerar o gráfico de faturamento mensal.")
        else:
            st.info("ℹ️ Não há dados de faturamento para o período selecionado.")
        
        # Dados de movimentações no período
        st.write("### Movimentações no Período")
        
        # Verifica se há dados para mostrar
        if not df_movimentacoes.empty and 'data' in df_movimentacoes.columns:
            # Filtra movimentações pelo período
            mov_periodo = df_movimentacoes[(df_movimentacoes['data'] >= periodo_inicio) & 
                                          (df_movimentacoes['data'] <= periodo_fim)]
            
            if not mov_periodo.empty:
                # Verifica se temos as colunas necessárias para a tabela
                colunas_necessarias = ['mes_ano', 'entrada', 'saida']
                colunas_disponiveis = all(col in mov_periodo.columns for col in colunas_necessarias)
                
                if colunas_disponiveis:
                    # Agrupar por mês/ano
                    try:
                        # Verifica quais colunas estão disponíveis para agregação
                        agg_columns = {}
                        if 'entrada' in mov_periodo.columns:
                            agg_columns['entrada'] = ['sum', 'mean', 'max']
                        if 'saida' in mov_periodo.columns:
                            agg_columns['saida'] = ['sum', 'mean', 'max']
                        
                        # Realiza a agregação
                        mov_stats = mov_periodo.groupby('mes_ano').agg(agg_columns)
                        
                        # Reinicia o índice para ter mes_ano como coluna
                        mov_stats = mov_stats.reset_index()
                        
                        # Criação da tabela de estatísticas com segurança
                        if 'mes_ano' in mov_stats.columns:
                            # Cria tabela formatada com as colunas que existem
                            stats_data = {'Mês/Ano': mov_stats['mes_ano']}
                            
                            # Adiciona as colunas de estatísticas que existem
                            if ('entrada', 'sum') in mov_stats.columns:
                                stats_data['Total Receitas (R$)'] = mov_stats[('entrada', 'sum')].apply(lambda x: f"{x:,.2f}")
                            elif 'entrada_sum' in mov_stats.columns:
                                stats_data['Total Receitas (R$)'] = mov_stats['entrada_sum'].apply(lambda x: f"{x:,.2f}")
                            
                            if ('entrada', 'mean') in mov_stats.columns:
                                stats_data['Média Receitas (R$)'] = mov_stats[('entrada', 'mean')].apply(lambda x: f"{x:,.2f}")
                            elif 'entrada_mean' in mov_stats.columns:
                                stats_data['Média Receitas (R$)'] = mov_stats['entrada_mean'].apply(lambda x: f"{x:,.2f}")
                            
                            if ('entrada', 'max') in mov_stats.columns:
                                stats_data['Maior Receita (R$)'] = mov_stats[('entrada', 'max')].apply(lambda x: f"{x:,.2f}")
                            elif 'entrada_max' in mov_stats.columns:
                                stats_data['Maior Receita (R$)'] = mov_stats['entrada_max'].apply(lambda x: f"{x:,.2f}")
                            
                            if ('saida', 'sum') in mov_stats.columns:
                                stats_data['Total Despesas (R$)'] = mov_stats[('saida', 'sum')].apply(lambda x: f"{x:,.2f}")
                            elif 'saida_sum' in mov_stats.columns:
                                stats_data['Total Despesas (R$)'] = mov_stats['saida_sum'].apply(lambda x: f"{x:,.2f}")
                            
                            if ('saida', 'mean') in mov_stats.columns:
                                stats_data['Média Despesas (R$)'] = mov_stats[('saida', 'mean')].apply(lambda x: f"{x:,.2f}")
                            elif 'saida_mean' in mov_stats.columns:
                                stats_data['Média Despesas (R$)'] = mov_stats['saida_mean'].apply(lambda x: f"{x:,.2f}")
                            
                            if ('saida', 'max') in mov_stats.columns:
                                stats_data['Maior Despesa (R$)'] = mov_stats[('saida', 'max')].apply(lambda x: f"{x:,.2f}")
                            elif 'saida_max' in mov_stats.columns:
                                stats_data['Maior Despesa (R$)'] = mov_stats['saida_max'].apply(lambda x: f"{x:,.2f}")
                            
                            # Cria e exibe a tabela
                            stats_table = pd.DataFrame(stats_data)
                            st.dataframe(stats_table, use_container_width=True)
                            
                            st.info("""
                            **Análise Estatística (Pereira da Silva, 2017)**: A tabela acima mostra a evolução mensal 
                            dos valores totais, médios e máximos de receitas e despesas. Estas informações são 
                            fundamentais para identificar padrões e anomalias no fluxo financeiro da agência.
                            """)
                        else:
                            st.info("ℹ️ Erro na estrutura dos dados agregados. Não foi possível mostrar estatísticas.")
                    except Exception as e:
                        st.info(f"ℹ️ Não foi possível gerar as estatísticas mensais. Erro: {str(e)}")
                else:
                    st.info("ℹ️ Os dados não contêm todas as colunas necessárias para a análise estatística.")
            else:
                st.info("ℹ️ Não há movimentações para o período selecionado.")
        else:
            st.info("ℹ️ Não há movimentações para análise.")
    
    # Botões no rodapé
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Importar Mais Dados"):
            st.switch_page("pages/importacao_dados.py")
    
    with col2:
        if st.button("Verificar Status do Banco"):
            st.switch_page("pages/db_status.py")

if __name__ == "__main__":
    main()