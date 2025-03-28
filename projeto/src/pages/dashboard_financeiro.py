import streamlit as st
import pandas as pd
import numpy as np
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
from models import Cliente, Servico, Despesa, Fatura, MovimentacaoBancaria, PlanoContas

def load_data():
    """Carrega todos os dados necessários para o dashboard"""
    db = get_db()
    try:
        # Carrega dados relevantes para análise financeira
        movimentacoes = db.query(MovimentacaoBancaria).all()
        plano_contas = db.query(PlanoContas).all()
        
        return {
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
    data = []
    for m in movimentacoes:
        data.append({
            'data': m.data,
            'mes': m.data.month,
            'ano': m.data.year,
            'mes_ano': f"{get_month_name(m.data.month)}/{m.data.year}",
            'filial': m.filial,
            'banco': m.banco,
            'natureza': m.natureza,
            'nome_natureza': m.nome_natureza,
            'categoria': m.categoria,
            'tipo_custo': m.tipo_custo,
            'entrada': m.entrada if m.entrada else 0,
            'saida': m.saida if m.saida else 0,
            'valor_liquido': (m.entrada if m.entrada else 0) - (m.saida if m.saida else 0),
            'historico': m.historico,
            'entidade': m.entidade,
            'documento_ref': m.documento_ref
        })
    return pd.DataFrame(data)

def plot_fluxo_caixa_mensal(df_movimentacoes):
    """Gráfico de fluxo de caixa mensal"""
    # Agrega por mês
    fluxo_mensal = df_movimentacoes.groupby(['ano', 'mes', 'mes_ano']).agg({
        'entrada': 'sum',
        'saida': 'sum',
        'valor_liquido': 'sum'
    }).reset_index()
    
    # Ordena por ano e mês
    fluxo_mensal = fluxo_mensal.sort_values(by=['ano', 'mes'])
    
    # Calcula o saldo acumulado
    fluxo_mensal['saldo_acumulado'] = fluxo_mensal['valor_liquido'].cumsum()
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras de entradas
    fig.add_trace(go.Bar(
        x=fluxo_mensal['mes_ano'],
        y=fluxo_mensal['entrada'],
        name='Entradas',
        marker_color='rgba(0, 128, 0, 0.7)'  # Verde
    ))
    
    # Adiciona barras de saídas
    fig.add_trace(go.Bar(
        x=fluxo_mensal['mes_ano'],
        y=fluxo_mensal['saida'] * -1,  # Inverte para mostrar como negativo
        name='Saídas',
        marker_color='rgba(220, 20, 60, 0.7)'  # Vermelho
    ))
    
    # Adiciona linha de saldo mensal
    fig.add_trace(go.Scatter(
        x=fluxo_mensal['mes_ano'],
        y=fluxo_mensal['valor_liquido'],
        name='Saldo Mensal',
        mode='lines+markers',
        line=dict(color='#000000', width=2)
    ))
    
    # Adiciona linha de saldo acumulado
    fig.add_trace(go.Scatter(
        x=fluxo_mensal['mes_ano'],
        y=fluxo_mensal['saldo_acumulado'],
        name='Saldo Acumulado',
        mode='lines+markers',
        line=dict(color='#4169E1', width=3, dash='dot')  # Azul
    ))
    
    # Layout
    fig.update_layout(
        title='Fluxo de Caixa Mensal',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        barmode='relative',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_distribuicao_categorias(df_movimentacoes):
    """Gráfico de distribuição por categorias contábeis"""
    # Agrupamento por categoria
    entradas_categoria = df_movimentacoes.groupby('categoria')['entrada'].sum().reset_index()
    saidas_categoria = df_movimentacoes.groupby('categoria')['saida'].sum().reset_index()
    
    # Configura visualização para entradas
    fig_entradas = px.pie(
        entradas_categoria,
        values='entrada',
        names='categoria',
        title='Distribuição de Receitas por Categoria',
        color_discrete_sequence=px.colors.sequential.Greens,
        hole=0.4
    )
    
    fig_entradas.update_traces(textposition='inside', textinfo='percent+label')
    
    # Configura visualização para saídas
    fig_saidas = px.pie(
        saidas_categoria,
        values='saida',
        names='categoria',
        title='Distribuição de Despesas por Categoria',
        color_discrete_sequence=px.colors.sequential.Reds,
        hole=0.4
    )
    
    fig_saidas.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig_entradas, fig_saidas

def plot_treemap_naturezas(df_movimentacoes, tipo='entrada'):
    """Gráfico treemap de entradas ou saídas por natureza"""
    # Determina qual valor usar
    valor_col = 'entrada' if tipo == 'entrada' else 'saida'
    
    # Filtra apenas valores positivos
    df_filtrado = df_movimentacoes[df_movimentacoes[valor_col] > 0].copy()
    
    if df_filtrado.empty:
        return None
    
    # Agrupamento hierárquico (categoria > nome_natureza)
    df_agrupado = df_filtrado.groupby(['categoria', 'nome_natureza'])[valor_col].sum().reset_index()
    
    # Determina cores e título com base no tipo
    if tipo == 'entrada':
        color_scale = 'Greens'
        titulo = 'Detalhamento de Receitas'
    else:
        color_scale = 'Reds'
        titulo = 'Detalhamento de Despesas'
    
    # Cria treemap
    fig = px.treemap(
        df_agrupado,
        path=['categoria', 'nome_natureza'],
        values=valor_col,
        title=titulo,
        color=valor_col,
        color_continuous_scale=color_scale
    )
    
    # Formata os valores como monetários
    fig.update_traces(
        texttemplate='%{label}<br>R$ %{value:,.2f}<br>%{percentRoot:.1%} do total',
        hovertemplate='%{label}<br>R$ %{value:,.2f}<br>%{percentRoot:.1%} do total'
    )
    
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25)
    )
    
    return fig

def plot_movimentacoes_filial(df_movimentacoes):
    """Gráfico de movimentações por filial"""
    # Agrupamento por filial
    mov_filial = df_movimentacoes.groupby('filial').agg({
        'entrada': 'sum',
        'saida': 'sum',
        'valor_liquido': 'sum'
    }).reset_index()
    
    # Ordena pelo valor líquido (decrescente)
    mov_filial = mov_filial.sort_values(by='valor_liquido', ascending=False)
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras de entrada
    fig.add_trace(go.Bar(
        x=mov_filial['filial'],
        y=mov_filial['entrada'],
        name='Entradas',
        marker_color='rgba(0, 128, 0, 0.7)'
    ))
    
    # Adiciona barras de saída
    fig.add_trace(go.Bar(
        x=mov_filial['filial'],
        y=mov_filial['saida'],
        name='Saídas',
        marker_color='rgba(220, 20, 60, 0.7)'
    ))
    
    # Adiciona linha de saldo
    fig.add_trace(go.Scatter(
        x=mov_filial['filial'],
        y=mov_filial['valor_liquido'],
        name='Saldo',
        mode='lines+markers',
        line=dict(color='#000000', width=2)
    ))
    
    # Layout
    fig.update_layout(
        title='Movimentações por Filial',
        xaxis_title='Filial',
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

def plot_timeline_movimentacoes(df_movimentacoes, periodo_inicio, periodo_fim):
    """Gráfico de timeline de movimentações"""
    # Filtra pelo período
    df_periodo = df_movimentacoes[(df_movimentacoes['data'] >= periodo_inicio) & 
                                   (df_movimentacoes['data'] <= periodo_fim)].copy()
    
    # Ordena por data
    df_periodo = df_periodo.sort_values(by='data')
    
    # Calcula o saldo acumulado
    df_periodo['saldo_acumulado'] = df_periodo['valor_liquido'].cumsum()
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona linha de saldo acumulado
    fig.add_trace(go.Scatter(
        x=df_periodo['data'],
        y=df_periodo['saldo_acumulado'],
        name='Saldo Acumulado',
        mode='lines',
        line=dict(color='#4169E1', width=2)
    ))
    
    # Adiciona pontos para entradas
    entradas = df_periodo[df_periodo['entrada'] > 0]
    if not entradas.empty:
        fig.add_trace(go.Scatter(
            x=entradas['data'],
            y=entradas['saldo_acumulado'],
            name='Entradas',
            mode='markers',
            marker=dict(
                color='rgba(0, 128, 0, 0.7)',
                size=entradas['entrada'] / entradas['entrada'].max() * 20,
                sizemin=5,
                sizemode='area',
                sizeref=2.*entradas['entrada'].max()/(20**2)
            ),
            hovertemplate='Data: %{x}<br>Entrada: R$ %{text:,.2f}<br>Saldo: R$ %{y:,.2f}',
            text=entradas['entrada']
        ))
    
    # Adiciona pontos para saídas
    saidas = df_periodo[df_periodo['saida'] > 0]
    if not saidas.empty:
        fig.add_trace(go.Scatter(
            x=saidas['data'],
            y=saidas['saldo_acumulado'],
            name='Saídas',
            mode='markers',
            marker=dict(
                color='rgba(220, 20, 60, 0.7)',
                size=saidas['saida'] / saidas['saida'].max() * 20,
                sizemin=5,
                sizemode='area',
                sizeref=2.*saidas['saida'].max()/(20**2)
            ),
            hovertemplate='Data: %{x}<br>Saída: R$ %{text:,.2f}<br>Saldo: R$ %{y:,.2f}',
            text=saidas['saida']
        ))
    
    # Layout
    fig.update_layout(
        title='Timeline de Movimentações e Saldo Acumulado',
        xaxis_title='Data',
        yaxis_title='Saldo Acumulado (R$)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='closest'
    )
    
    return fig

def plot_analise_custos_fixos_variaveis(df_movimentacoes):
    """Gráfico de análise de custos fixos vs variáveis"""
    # Filtra apenas saídas
    df_saidas = df_movimentacoes[df_movimentacoes['saida'] > 0].copy()
    
    if df_saidas.empty:
        return None
    
    # Agrupa por tipo de custo e mês
    custos_mensais = df_saidas.groupby(['ano', 'mes', 'mes_ano', 'tipo_custo'])['saida'].sum().reset_index()
    
    # Pivot para ter fixos e variáveis lado a lado
    custos_pivot = custos_mensais.pivot_table(
        index=['ano', 'mes', 'mes_ano'],
        columns='tipo_custo',
        values='saida',
        aggfunc='sum'
    ).reset_index().fillna(0)
    
    # Renomeia as colunas
    if 'Fixo' not in custos_pivot.columns:
        custos_pivot['Fixo'] = 0
    if 'Variável' not in custos_pivot.columns:
        custos_pivot['Variável'] = 0
    
    # Ordena por ano e mês
    custos_pivot = custos_pivot.sort_values(by=['ano', 'mes'])
    
    # Calcula totais para análise
    custos_pivot['Total'] = custos_pivot['Fixo'] + custos_pivot['Variável']
    custos_pivot['% Fixos'] = custos_pivot['Fixo'] / custos_pivot['Total'] * 100
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras de custos fixos
    fig.add_trace(go.Bar(
        x=custos_pivot['mes_ano'],
        y=custos_pivot['Fixo'],
        name='Custos Fixos',
        marker_color='rgba(65, 105, 225, 0.7)'  # Azul
    ))
    
    # Adiciona barras de custos variáveis
    fig.add_trace(go.Bar(
        x=custos_pivot['mes_ano'],
        y=custos_pivot['Variável'],
        name='Custos Variáveis',
        marker_color='rgba(255, 165, 0, 0.7)'  # Laranja
    ))
    
    # Adiciona linha de percentual de custos fixos
    fig.add_trace(go.Scatter(
        x=custos_pivot['mes_ano'],
        y=custos_pivot['% Fixos'],
        name='% Custos Fixos',
        mode='lines+markers',
        line=dict(color='#000000', width=2),
        yaxis='y2'
    ))
    
    # Layout com eixo y secundário
    fig.update_layout(
        title='Análise de Custos Fixos vs. Variáveis',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        yaxis2=dict(
            title='% Custos Fixos',
            titlefont=dict(color='#000000'),
            tickfont=dict(color='#000000'),
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_sazonalidade(df_movimentacoes):
    """Gráfico de sazonalidade por mês"""
    # Agrupa por mês (ignorando o ano)
    sazonalidade = df_movimentacoes.groupby('mes').agg({
        'entrada': 'sum',
        'saida': 'sum',
        'valor_liquido': 'sum'
    }).reset_index()
    
    # Ordena por mês
    sazonalidade = sazonalidade.sort_values(by='mes')
    
    # Adiciona nomes dos meses
    sazonalidade['mes_nome'] = sazonalidade['mes'].apply(lambda x: get_month_name(x))
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona área de entradas
    fig.add_trace(go.Scatter(
        x=sazonalidade['mes_nome'],
        y=sazonalidade['entrada'],
        name='Entradas',
        mode='lines+markers',
        line=dict(color='rgba(0, 128, 0, 0.7)', width=2),
        fill='tozeroy'
    ))
    
    # Adiciona área de saídas
    fig.add_trace(go.Scatter(
        x=sazonalidade['mes_nome'],
        y=sazonalidade['saida'],
        name='Saídas',
        mode='lines+markers',
        line=dict(color='rgba(220, 20, 60, 0.7)', width=2),
        fill='tozeroy'
    ))
    
    # Adiciona linha de resultado líquido
    fig.add_trace(go.Scatter(
        x=sazonalidade['mes_nome'],
        y=sazonalidade['valor_liquido'],
        name='Resultado Líquido',
        mode='lines+markers',
        line=dict(color='#000000', width=3)
    ))
    
    # Layout
    fig.update_layout(
        title='Análise de Sazonalidade',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_indicadores_mensais(df_movimentacoes):
    """Gráfico de indicadores mensais"""
    # Agrega por mês
    indicadores_mensais = df_movimentacoes.groupby(['ano', 'mes', 'mes_ano']).agg({
        'entrada': 'sum',
        'saida': 'sum',
        'valor_liquido': 'sum'
    }).reset_index()
    
    # Ordena por ano e mês
    indicadores_mensais = indicadores_mensais.sort_values(by=['ano', 'mes'])
    
    # Calcula indicadores
    indicadores_mensais['margem'] = indicadores_mensais.apply(
        lambda x: 0 if x['entrada'] == 0 else (x['valor_liquido'] / x['entrada']) * 100,
        axis=1
    )
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras de entradas
    fig.add_trace(go.Bar(
        x=indicadores_mensais['mes_ano'],
        y=indicadores_mensais['entrada'],
        name='Receitas',
        marker_color='rgba(0, 128, 0, 0.7)'
    ))
    
    # Adiciona barras de saídas
    fig.add_trace(go.Bar(
        x=indicadores_mensais['mes_ano'],
        y=indicadores_mensais['saida'],
        name='Despesas',
        marker_color='rgba(220, 20, 60, 0.7)'
    ))
    
    # Adiciona linha de margem
    fig.add_trace(go.Scatter(
        x=indicadores_mensais['mes_ano'],
        y=indicadores_mensais['margem'],
        name='Margem (%)',
        mode='lines+markers',
        line=dict(color='#000000', width=2),
        yaxis='y2'
    ))
    
    # Layout com eixo y secundário
    fig.update_layout(
        title='Indicadores Mensais',
        xaxis_title='Mês/Ano',
        yaxis_title='Valor (R$)',
        yaxis2=dict(
            title='Margem (%)',
            titlefont=dict(color='#000000'),
            tickfont=dict(color='#000000'),
            overlaying='y',
            side='right',
            range=[min(0, indicadores_mensais['margem'].min() - 10), max(100, indicadores_mensais['margem'].max() + 10)]
        ),
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

def calcular_kpis(df_movimentacoes, periodo_inicio, periodo_fim):
    """Calcula KPIs para o período selecionado"""
    # Filtra pelo período
    df_periodo = df_movimentacoes[(df_movimentacoes['data'] >= periodo_inicio) & 
                                  (df_movimentacoes['data'] <= periodo_fim)]
    
    # Receitas e despesas
    total_receitas = df_periodo['entrada'].sum()
    total_despesas = df_periodo['saida'].sum()
    resultado_periodo = total_receitas - total_despesas
    
    # Margem e outros indicadores
    margem = 0 if total_receitas == 0 else (resultado_periodo / total_receitas) * 100
    
    # Custos fixos e variáveis
    df_custos = df_periodo[df_periodo['saida'] > 0]
    custos_fixos = df_custos[df_custos['tipo_custo'] == 'Fixo']['saida'].sum()
    custos_variaveis = df_custos[df_custos['tipo_custo'] == 'Variável']['saida'].sum()
    
    # Índice de fixação de despesas (Martins, 2018)
    indice_fixacao = 0 if total_despesas == 0 else (custos_fixos / total_despesas) * 100
    
    return {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'resultado_periodo': resultado_periodo,
        'margem': margem,
        'custos_fixos': custos_fixos,
        'custos_variaveis': custos_variaveis,
        'indice_fixacao': indice_fixacao
    }

def main():
    st.title("Dashboard Financeiro Otimizado")
    st.write("Análise completa de movimentações financeiras da agência")
    
    # Verifica conexão com o banco
    with st.spinner("Verificando conexão com o banco de dados..."):
        connection_result = test_connection()
    
    if not connection_result:
        st.error("❌ Não foi possível conectar ao banco de dados!")
        return
    
    # Carrega os dados
    with st.spinner("Carregando dados..."):
        data = load_data()
    
    if not data:
        st.error("❌ Não foi possível carregar os dados!")
        return
    
    # Extrai os dados carregados
    movimentacoes = data['movimentacoes']
    
    # Converte para DataFrame
    df_movimentacoes = create_movimentacoes_df(movimentacoes)
    
    if df_movimentacoes.empty:
        st.warning("⚠️ Não há movimentações bancárias registradas. Por favor, importe dados.")
        return
    
    # Filtros no sidebar
    st.sidebar.header("Filtros")
    
    # Filtro de período
    data_min = df_movimentacoes['data'].min()
    data_max = df_movimentacoes['data'].max()
    
    periodo_inicio = st.sidebar.date_input("Data Início", value=data_min)
    periodo_fim = st.sidebar.date_input("Data Fim", value=data_max)
    
    # Filtro de filial
    filiais = ['Todas'] + sorted(df_movimentacoes['filial'].unique().tolist())
    filial_selecionada = st.sidebar.selectbox("Filial", filiais)
    
    # Filtro de categoria
    categorias = ['Todas'] + sorted(df_movimentacoes['categoria'].unique().tolist())
    categoria_selecionada = st.sidebar.selectbox("Categoria", categorias)
    
    # Aplica filtros
    df_filtrado = df_movimentacoes.copy()
    
    # Filtro de período
    df_filtrado = df_filtrado[(df_filtrado['data'] >= periodo_inicio) & 
                              (df_filtrado['data'] <= periodo_fim)]
    
    # Filtro de filial
    if filial_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['filial'] == filial_selecionada]
    
    # Filtro de categoria
    if categoria_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_selecionada]
    
    # Calcula KPIs
    kpis = calcular_kpis(df_filtrado, periodo_inicio, periodo_fim)
    
    # Layout em abas
    tab1, tab2, tab3, tab4 = st.tabs([
        "Visão Geral", 
        "Análise Detalhada", 
        "Fluxo de Caixa",
        "Detalhamento por Categoria"
    ])
    
    with tab1:
        st.subheader("Indicadores do Período")
        
        # KPIs em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Receitas Totais",
                value=f"R$ {kpis['total_receitas']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Despesas Totais",
                value=f"R$ {kpis['total_despesas']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Resultado do Período",
                value=f"R$ {kpis['resultado_periodo']:,.2f}",
                delta=f"{kpis['margem']:.2f}%" if kpis['margem'] != 0 else None,
                delta_color="normal"
            )
        
        # Segunda linha de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Custos Fixos",
                value=f"R$ {kpis['custos_fixos']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Custos Variáveis",
                value=f"R$ {kpis['custos_variaveis']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Índice de Fixação de Despesas",
                value=f"{kpis['indice_fixacao']:.2f}%",
                help="Percentual das despesas totais que são fixas (Martins, 2018)"
            )
        
        # Gráfico de indicadores mensais
        st.subheader("Indicadores Mensais")
        
        fig_indicadores = plot_indicadores_mensais(df_filtrado)
        st.plotly_chart(fig_indicadores, use_container_width=True)
        
        st.info("""
        **Índice de Fixação de Despesas**: Representa a proporção de custos fixos em relação ao total de despesas.
        Um índice elevado (acima de 70%) indica menor flexibilidade operacional e maior risco em períodos de baixa receita.
        """)
        
        # Gráfico de distribuição por categorias
        st.subheader("Distribuição por Categorias")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_entradas, fig_saidas = plot_distribuicao_categorias(df_filtrado)
            st.plotly_chart(fig_entradas, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_saidas, use_container_width=True)
    
    with tab2:
        st.subheader("Análise por Filial")
        
        # Gráfico de movimentações por filial
        fig_filial = plot_movimentacoes_filial(df_filtrado)
        st.plotly_chart(fig_filial, use_container_width=True)
        
        # Análise de custos fixos vs variáveis
        st.subheader("Custos Fixos vs. Variáveis")
        
        fig_custos = plot_analise_custos_fixos_variaveis(df_filtrado)
        if fig_custos:
            st.plotly_chart(fig_custos, use_container_width=True)
        else:
            st.info("Não há dados de custos para o período selecionado.")
        
        # Análise de sazonalidade
        st.subheader("Sazonalidade")
        
        fig_sazonalidade = plot_sazonalidade(df_filtrado)
        st.plotly_chart(fig_sazonalidade, use_container_width=True)
        
        st.info("""
        **Análise de Sazonalidade**: Mostra padrões recorrentes de receitas e despesas ao longo do ano,
        independentemente do ano específico. Útil para planejamento e previsão financeira.
        """)
    
    with tab3:
        st.subheader("Fluxo de Caixa")
        
        # Gráfico de fluxo de caixa mensal
        fig_fluxo = plot_fluxo_caixa_mensal(df_filtrado)
        st.plotly_chart(fig_fluxo, use_container_width=True)
        
        # Timeline de movimentações
        st.subheader("Timeline de Movimentações")
        
        fig_timeline = plot_timeline_movimentacoes(df_filtrado, periodo_inicio, periodo_fim)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.info("""
        **Timeline de Movimentações**: Cada ponto representa uma transação. O tamanho do ponto é proporcional ao valor.
        Pontos verdes são entradas e pontos vermelhos são saídas. A linha azul mostra o saldo acumulado ao longo do tempo.
        """)
        
        # Tabela de movimentações recentes
        st.subheader("Movimentações Recentes")
        
        mov_recentes = df_filtrado.sort_values(by='data', ascending=False).head(10)
        
        if not mov_recentes.empty:
            tabela_recentes = mov_recentes[['data', 'nome_natureza', 'entrada', 'saida', 'historico']].copy()
            
            # Formata valores monetários
            tabela_recentes['entrada'] = tabela_recentes['entrada'].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "")
            tabela_recentes['saida'] = tabela_recentes['saida'].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "")
            
            # Renomeia colunas
            tabela_recentes.columns = ['Data', 'Natureza', 'Entrada', 'Saída', 'Histórico']
            
            st.table(tabela_recentes)
        else:
            st.info("Não há movimentações para o período selecionado.")
    
    with tab4:
        st.subheader("Detalhamento de Receitas")
        
        # Treemap de receitas
        fig_treemap_receitas = plot_treemap_naturezas(df_filtrado, tipo='entrada')
        if fig_treemap_receitas:
            st.plotly_chart(fig_treemap_receitas, use_container_width=True)
        else:
            st.info("Não há dados de receitas para o período selecionado.")
        
        st.subheader("Detalhamento de Despesas")
        
        # Treemap de despesas
        fig_treemap_despesas = plot_treemap_naturezas(df_filtrado, tipo='saida')
        if fig_treemap_despesas:
            st.plotly_chart(fig_treemap_despesas, use_container_width=True)
        else:
            st.info("Não há dados de despesas para o período selecionado.")
        
        st.info("""
        **Visualização Treemap**: O tamanho de cada retângulo representa o valor proporcional da receita ou despesa.
        A hierarquia mostra a categoria principal e a natureza específica, facilitando a identificação dos principais
        componentes do resultado financeiro.
        """)

if __name__ == "__main__":
    main()