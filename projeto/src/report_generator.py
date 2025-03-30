import os
import io
import base64
from datetime import datetime
import pandas as pd
import tempfile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import PageBreak, KeepTogether
from reportlab.lib.units import cm, mm, inch
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart


class FinancialReportGenerator:
    """
    Classe para geração de relatórios financeiros em PDF a partir dos dados do dashboard.
    """
    def __init__(self, dados_metricas, periodo_inicio, periodo_fim, dados_adicionais=None):
        """
        Inicializa o gerador de relatórios com os dados necessários.
        
        Args:
            dados_metricas (dict): Dicionário com os dados das métricas calculadas
            periodo_inicio (date): Data de início do período analisado
            periodo_fim (date): Data de fim do período analisado
            dados_adicionais (dict, optional): Dados adicionais para o relatório
        """
        self.dados_metricas = dados_metricas
        self.periodo_inicio = periodo_inicio
        self.periodo_fim = periodo_fim
        self.dados_adicionais = dados_adicionais or {}
        self.styles = getSampleStyleSheet()
        
        # Adiciona estilos personalizados
        self.styles.add(ParagraphStyle(
            name='Titulo',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=1,  # Centralizado
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=1,  # Centralizado
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='NormalPersonalizado',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='TextoCentralizado',
            parent=self.styles['Normal'],
            alignment=1,  # Centralizado
            fontSize=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='Indicador',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=1,
            spaceBefore=4,
            spaceAfter=6,
            textColor=colors.darkblue
        ))
        
        # Define a paleta de cores
        self.paleta = [
            colors.green, colors.red, colors.blue, 
            colors.orange, colors.purple, colors.teal
        ]
    
    def formatar_valor(self, valor, eh_percentual=False):
        """Formata um valor para exibição no relatório"""
        if eh_percentual:
            return f"{valor:.2f}%"
        else:
            return f"R$ {valor:,.2f}"
    
    def gerar_cabecalho(self):
        """Gera os elementos do cabeçalho do relatório"""
        elementos = []
        
        # Título principal
        elementos.append(Paragraph("Relatório Financeiro - Agência de Publicidade", self.styles['Titulo']))
        
        # Subtítulo com o período
        subtitulo = f"Período: {self.periodo_inicio.strftime('%d/%m/%Y')} a {self.periodo_fim.strftime('%d/%m/%Y')}"
        elementos.append(Paragraph(subtitulo, self.styles['Subtitulo']))
        
        # Data de geração
        data_geracao = f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elementos.append(Paragraph(data_geracao, self.styles['TextoCentralizado']))
        
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def gerar_metricas_principais(self):
        """Gera a seção de métricas principais do relatório"""
        elementos = []
        
        # Título da seção
        elementos.append(Paragraph("Indicadores Financeiros", self.styles['Heading2']))
        elementos.append(Spacer(1, 10))
        
        # Tabela de métricas principais
        dados_tabela = [
            ["Indicador", "Valor"],
            ["Receitas Totais", self.formatar_valor(self.dados_metricas['total_receitas'])],
            ["Despesas Totais", self.formatar_valor(self.dados_metricas['total_despesas'])],
            ["Saldo do Período", self.formatar_valor(self.dados_metricas['saldo'])],
            ["Margem de Lucro", self.formatar_valor(self.dados_metricas['margem_lucro'], True)],
            ["Custos Fixos", self.formatar_valor(self.dados_metricas['custos_fixos'])],
            ["Custos Variáveis", self.formatar_valor(self.dados_metricas['custos_variaveis'])],
            ["Índice de Fixação", self.formatar_valor(self.dados_metricas['indice_fixacao'], True)]
        ]
        
        # Cria a tabela
        tabela = Table(dados_tabela, colWidths=[250, 200])
        
        # Estilo da tabela
        estilo_tabela = TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONT', (0, 0), (1, 0), 'Helvetica-Bold', 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 8),
            ('BACKGROUND', (0, -1), (1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ])
        
        # Alterna cores nas linhas
        for i in range(1, len(dados_tabela)):
            if i % 2 == 0:
                estilo_tabela.add('BACKGROUND', (0, i), (1, i), colors.whitesmoke)
        
        tabela.setStyle(estilo_tabela)
        elementos.append(tabela)
        
        # Adiciona interpretação
        elementos.append(Spacer(1, 15))
        interpretacao = "Análise: "
        
        # Interpreta o índice de fixação
        indice = self.dados_metricas['indice_fixacao']
        if indice > 70:
            interpretacao += f"O índice de fixação de {indice:.1f}% indica uma estrutura de custos RÍGIDA, "
            interpretacao += "com alta proporção de custos fixos. Isso representa maior risco em períodos de baixa receita."
        elif indice < 30:
            interpretacao += f"O índice de fixação de {indice:.1f}% indica uma estrutura de custos FLEXÍVEL, "
            interpretacao += "com baixa proporção de custos fixos. Isso representa menor risco em períodos de baixa receita."
        else:
            interpretacao += f"O índice de fixação de {indice:.1f}% indica uma estrutura de custos MODERADA, "
            interpretacao += "com equilíbrio entre custos fixos e variáveis."
        
        elementos.append(Paragraph(interpretacao, self.styles['NormalPersonalizado']))
        
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def gerar_analise_custos(self):
        """Gera a seção de análise de custos do relatório"""
        elementos = []
        
        elementos.append(Paragraph("Análise de Custos", self.styles['Heading2']))
        elementos.append(Spacer(1, 10))
        
        # Cria um gráfico de pizza para custos fixos vs variáveis
        custos_fixos = self.dados_metricas['custos_fixos']
        custos_variaveis = self.dados_metricas['custos_variaveis']
        
        # Só cria o gráfico se houver dados
        if custos_fixos > 0 or custos_variaveis > 0:
            # Cria o desenho para o gráfico
            d = Drawing(400, 200)
            
            # Cria o gráfico de pizza
            pc = Pie()
            pc.x = 150
            pc.y = 50
            pc.width = 150
            pc.height = 150
            pc.data = [custos_fixos, custos_variaveis]
            pc.labels = ['Custos Fixos', 'Custos Variáveis']
            pc.slices.strokeWidth = 0.5
            pc.slices[0].fillColor = colors.lightblue
            pc.slices[1].fillColor = colors.lightgreen
            
            d.add(pc)
            elementos.append(d)
            
            # Adiciona legenda
            legenda = "Distribuição dos Custos: "
            total_custos = custos_fixos + custos_variaveis
            
            if total_custos > 0:
                pct_fixos = (custos_fixos / total_custos) * 100
                pct_variaveis = (custos_variaveis / total_custos) * 100
                legenda += f"Fixos {pct_fixos:.1f}%, Variáveis {pct_variaveis:.1f}%"
                elementos.append(Paragraph(legenda, self.styles['TextoCentralizado']))
                # Reduz o espaço após o gráfico
                elementos.append(Spacer(1, 5))
        else:
            elementos.append(Paragraph("Não há dados suficientes para análise de custos.", self.styles['NormalPersonalizado']))
        
        # Adiciona informações sobre o ponto de equilíbrio
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph("Ponto de Equilíbrio", self.styles['Heading3']))
        
        # Calcula ponto de equilíbrio (se possível)
        if (self.dados_metricas['total_receitas'] > 0 and 
            self.dados_metricas['custos_variaveis'] < self.dados_metricas['total_receitas']):
            
            # Calcula margem de contribuição
            margem_contribuicao = self.dados_metricas['total_receitas'] - self.dados_metricas['custos_variaveis']
            indice_mc = margem_contribuicao / self.dados_metricas['total_receitas']
            
            # Ponto de equilíbrio
            pe = self.dados_metricas['custos_fixos'] / indice_mc if indice_mc > 0 else 0
            
            texto_pe = f"Ponto de Equilíbrio: {self.formatar_valor(pe)}"
            elementos.append(Paragraph(texto_pe, self.styles['Indicador']))
            
            # Verifica se está acima do ponto de equilíbrio
            if self.dados_metricas['total_receitas'] > pe:
                folga = self.dados_metricas['total_receitas'] - pe
                analise = f"A agência está ACIMA do ponto de equilíbrio, com folga de {self.formatar_valor(folga)}."
                elementos.append(Paragraph(analise, self.styles['NormalPersonalizado']))
            else:
                deficit = pe - self.dados_metricas['total_receitas']
                analise = f"A agência está ABAIXO do ponto de equilíbrio, com déficit de {self.formatar_valor(deficit)}."
                elementos.append(Paragraph(analise, self.styles['Normal']))
            
            # Explicação do cálculo
            explicacao = (
                "O Ponto de Equilíbrio representa a receita necessária para cobrir todos os custos, "
                "sem gerar lucro ou prejuízo. É calculado dividindo os Custos Fixos pelo Índice de "
                "Margem de Contribuição (Receita - Custos Variáveis) ÷ Receita."
            )
            elementos.append(Paragraph(explicacao, self.styles['NormalPersonalizado']))
        else:
            elementos.append(Paragraph(
                "Não foi possível calcular o ponto de equilíbrio. É necessário ter receitas positivas "
                "e custos variáveis menores que as receitas.",
                self.styles['NormalPersonalizado']
            ))
        
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def gerar_analise_despesas(self):
        """Gera a seção de análise de despesas do relatório"""
        elementos = []
        
        # Reduz o espaçamento antes da seção para melhorar o uso do espaço
        elementos.append(Spacer(1, 5))
        elementos.append(Paragraph("Análise de Despesas por Categoria", self.styles['Heading2']))
        elementos.append(Spacer(1, 8))
        
        # Verifica se há dados de despesas por categoria
        despesas_por_categoria = self.dados_metricas.get('despesas_por_categoria', pd.DataFrame())
        
        if not despesas_por_categoria.empty and 'categoria' in despesas_por_categoria.columns and 'valor' in despesas_por_categoria.columns:
            # Ordena as despesas por valor (decrescente)
            despesas_por_categoria = despesas_por_categoria.sort_values(by='valor', ascending=False)
            
            # Prepara dados para a tabela
            dados_tabela = [["Categoria", "Valor", "% do Total"]]
            
            # Calcula o total
            total_despesas = despesas_por_categoria['valor'].sum()
            
            # Adiciona cada categoria à tabela
            for _, row in despesas_por_categoria.iterrows():
                categoria = row['categoria']
                valor = row['valor']
                percentual = (valor / total_despesas * 100) if total_despesas > 0 else 0
                
                dados_tabela.append([
                    categoria,
                    self.formatar_valor(valor),
                    f"{percentual:.2f}%"
                ])
            
            # Adiciona linha de total
            dados_tabela.append(["TOTAL", self.formatar_valor(total_despesas), "100.00%"])
            
            # Cria a tabela
            tabela = Table(dados_tabela, colWidths=[200, 150, 100])
            
            # Estilo da tabela
            estilo_tabela = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
                ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 10),
            ])
            
            # Alterna cores nas linhas
            for i in range(1, len(dados_tabela)-1):
                if i % 2 == 0:
                    estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
            
            tabela.setStyle(estilo_tabela)
            elementos.append(tabela)
            
            # Adiciona interpretação da análise vertical
            elementos.append(Spacer(1, 15))
            elementos.append(Paragraph(
                "A análise vertical das despesas (Pereira da Silva, 2017) permite identificar as "
                "categorias mais significativas em termos de consumo de recursos financeiros, "
                "facilitando decisões gerenciais de controle de custos e otimização.", 
                self.styles['NormalPersonalizado']
            ))
            
            # Identifica as maiores categorias
            if len(despesas_por_categoria) > 0:
                maior_categoria = despesas_por_categoria.iloc[0]['categoria']
                maior_valor = despesas_por_categoria.iloc[0]['valor']
                maior_pct = (maior_valor / total_despesas * 100) if total_despesas > 0 else 0
                
                elementos.append(Paragraph(
                    f"A categoria '{maior_categoria}' representa {maior_pct:.2f}% do total de despesas, "
                    f"sendo a mais significativa no período analisado.",
                    self.styles['NormalPersonalizado']
                ))
        else:
            elementos.append(Paragraph(
                "Não há dados suficientes para análise de despesas por categoria.",
                self.styles['NormalPersonalizado']
            ))
        
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def gerar_analise_temporal(self):
        """Gera a seção de análise temporal do relatório"""
        elementos = []
        
        elementos.append(Paragraph("Análise Temporal", self.styles['Heading2']))
        elementos.append(Spacer(1, 8))
        
        # Faturamento mensal com altura reduzida
        elementos.append(Paragraph("Evolução do Faturamento", self.styles['Heading3']))
        elementos.append(Spacer(1, 5))
        
        faturamento_mensal = self.dados_metricas.get('faturamento_mensal', pd.DataFrame())
        
        if not faturamento_mensal.empty and 'mes_ano' in faturamento_mensal.columns and 'valor' in faturamento_mensal.columns:
            # Simplifica para no máximo 12 meses para o gráfico ficar legível
            if len(faturamento_mensal) > 12:
                faturamento_mensal = faturamento_mensal.tail(12)
            
            # Prepara dados para o gráfico
            labels = faturamento_mensal['mes_ano'].tolist()
            data = faturamento_mensal['valor'].tolist()
            
            # Cria um gráfico de linhas (reduzido em altura para economizar espaço)
            desenho = Drawing(500, 180)
            
            # Cria o gráfico
            grafico = HorizontalLineChart()
            grafico.x = 50
            grafico.y = 50
            grafico.height = 110
            grafico.width = 400
            grafico.data = [data]
            
            # Configura os eixos
            grafico.categoryAxis.categoryNames = labels
            grafico.categoryAxis.labels.boxAnchor = 'ne'
            grafico.categoryAxis.labels.angle = 30
            grafico.valueAxis.valueMin = 0
            
            # Adiciona o gráfico ao desenho
            desenho.add(grafico)
            elementos.append(desenho)
            
            # Adiciona interpretação
            if len(faturamento_mensal) >= 2:
                primeiro_valor = faturamento_mensal['valor'].iloc[0]
                ultimo_valor = faturamento_mensal['valor'].iloc[-1]
                
                variacao = ((ultimo_valor / primeiro_valor) - 1) * 100 if primeiro_valor > 0 else 0
                
                if variacao > 10:
                    analise = f"Observa-se uma tendência de CRESCIMENTO de {variacao:.2f}% no faturamento durante o período analisado."
                    elementos.append(Paragraph(analise, self.styles['NormalPersonalizado']))
                elif variacao < -10:
                    analise = f"Observa-se uma tendência de QUEDA de {abs(variacao):.2f}% no faturamento durante o período analisado."
                    elementos.append(Paragraph(analise, self.styles['NormalPersonalizado']))
                else:
                    analise = f"Observa-se uma tendência de ESTABILIDADE no faturamento durante o período analisado, com variação de {variacao:.2f}%."
                    elementos.append(Paragraph(analise, self.styles['NormalPersonalizado']))
        else:
            elementos.append(Paragraph(
                "Não há dados suficientes para análise da evolução do faturamento.",
                self.styles['NormalPersonalizado']
            ))
        
        # Receitas vs Despesas
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph("Receitas vs Despesas", self.styles['Heading3']))
        
        receitas_despesas_mes = self.dados_metricas.get('receitas_despesas_mes', pd.DataFrame())
        
        if not receitas_despesas_mes.empty and 'mes_ano' in receitas_despesas_mes.columns:
            if 'entrada' in receitas_despesas_mes.columns and 'saida' in receitas_despesas_mes.columns:
                # Simplifica para no máximo 6 meses para a tabela ficar compacta
                if len(receitas_despesas_mes) > 6:
                    receitas_despesas_mes = receitas_despesas_mes.tail(6)
                
                # Prepara dados para a tabela
                dados_tabela = [["Mês/Ano", "Receitas", "Despesas", "Saldo"]]
                
                for _, row in receitas_despesas_mes.iterrows():
                    mes_ano = row['mes_ano']
                    entrada = row['entrada']
                    saida = row['saida']
                    saldo = entrada - saida
                    
                    dados_tabela.append([
                        mes_ano,
                        self.formatar_valor(entrada),
                        self.formatar_valor(saida),
                        self.formatar_valor(saldo)
                    ])
                
                # Cria a tabela
                tabela = Table(dados_tabela, colWidths=[100, 120, 120, 120])
                
                # Estilo da tabela
                estilo_tabela = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ])
                
                # Alterna cores nas linhas
                for i in range(1, len(dados_tabela)):
                    if i % 2 == 0:
                        estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
                    
                    # Destaca saldos negativos
                    if i > 0:
                        saldo_str = dados_tabela[i][3]
                        if "-" in saldo_str:
                            estilo_tabela.add('TEXTCOLOR', (3, i), (3, i), colors.red)
                
                tabela.setStyle(estilo_tabela)
                elementos.append(tabela)
                
                # Adiciona interpretação
                elementos.append(Spacer(1, 5))
                elementos.append(Paragraph(
                    "A análise temporal de receitas e despesas (Pereira da Silva, 2017) permite identificar "
                    "tendências, sazonalidades e pontos críticos no fluxo financeiro da agência.",
                    self.styles['NormalPersonalizado']
                ))
            else:
                elementos.append(Paragraph(
                    "Dados de receitas ou despesas ausentes para geração da tabela comparativa.",
                    self.styles['NormalPersonalizado']
                ))
        else:
            elementos.append(Paragraph(
                "Não há dados suficientes para análise comparativa de receitas e despesas.",
                self.styles['NormalPersonalizado']
            ))
        
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def gerar_consideracoes_finais(self):
        """Gera as considerações finais do relatório"""
        elementos = []
        
        # Adicionamos um pequeno espaço para separar visualmente da seção anterior
        elementos.append(Spacer(1, 15))
        elementos.append(Paragraph("Considerações Finais", self.styles['Heading2']))
        elementos.append(Spacer(1, 5))
        
        # Avaliação geral baseada nos dados financeiros
        margem_lucro = self.dados_metricas['margem_lucro']
        indice_fixacao = self.dados_metricas['indice_fixacao']
        saldo = self.dados_metricas['saldo']
        
        consideracoes = []
        
        # Avaliação da margem de lucro
        if margem_lucro > 20:
            consideracoes.append(
                f"A margem de lucro de {margem_lucro:.2f}% está em um nível EXCELENTE, indicando "
                "alta eficiência operacional e precificação adequada dos serviços."
            )
        elif margem_lucro > 10:
            consideracoes.append(
                f"A margem de lucro de {margem_lucro:.2f}% está em um nível BOM, indicando "
                "operações saudáveis, mas com espaço para otimização."
            )
        elif margem_lucro > 0:
            consideracoes.append(
                f"A margem de lucro de {margem_lucro:.2f}% está em um nível REGULAR, sugerindo "
                "a necessidade de revisão da estrutura de custos e/ou precificação."
            )
        else:
            consideracoes.append(
                f"A margem de lucro de {margem_lucro:.2f}% está NEGATIVA, indicando uma situação "
                "de prejuízo que requer atenção imediata na reestruturação do negócio."
            )
        
        # Avaliação da estrutura de custos
        if indice_fixacao > 70:
            consideracoes.append(
                f"O índice de fixação de {indice_fixacao:.2f}% indica uma estrutura de custos RÍGIDA. "
                "Recomenda-se avaliar possibilidades de flexibilização para reduzir riscos em períodos de baixas receitas."
            )
        elif indice_fixacao < 30:
            consideracoes.append(
                f"O índice de fixação de {indice_fixacao:.2f}% indica uma estrutura de custos FLEXÍVEL, "
                "representando menor risco em períodos de flutuação de receitas."
            )
        else:
            consideracoes.append(
                f"O índice de fixação de {indice_fixacao:.2f}% indica uma estrutura de custos EQUILIBRADA "
                "entre componentes fixos e variáveis."
            )
        
        # Avaliação do resultado do período
        if saldo > 0:
            consideracoes.append(
                f"O resultado positivo do período ({self.formatar_valor(saldo)}) demonstra "
                "uma gestão financeira eficaz e operações lucrativas."
            )
        else:
            consideracoes.append(
                f"O resultado negativo do período ({self.formatar_valor(saldo)}) indica "
                "a necessidade de ajustes na operação para retornar à lucratividade."
            )
        
        # Adiciona as considerações ao relatório
        for consideracao in consideracoes:
            elementos.append(Paragraph(consideracao, self.styles['NormalPersonalizado']))
            elementos.append(Spacer(1, 3))
        
        # Recomendações
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph("Recomendações", self.styles['Heading3']))
        
        # Gera recomendações baseadas nos dados
        recomendacoes = []
        
        if margem_lucro < 10:
            recomendacoes.append(
                "Revisar a precificação dos serviços para melhorar a margem de lucro."
            )
        
        if indice_fixacao > 70:
            recomendacoes.append(
                "Avaliar a possibilidade de terceirizar algumas atividades para reduzir custos fixos."
            )
        
        if saldo < 0:
            recomendacoes.append(
                "Implementar medidas de controle de despesas e aumento da eficiência operacional."
            )
        
        # Recomendações padrão
        recomendacoes.extend([
            "Realizar análises mensais de indicadores financeiros para acompanhamento contínuo.",
            "Manter um fundo de reserva para enfrentar períodos de baixa sazonalidade.",
            "Avaliar regularmente o portfólio de serviços, priorizando aqueles de maior rentabilidade."
        ])
        
        # Adiciona as recomendações como itens
        for i, recomendacao in enumerate(recomendacoes):
            elementos.append(Paragraph(f"{i+1}. {recomendacao}", self.styles['NormalPersonalizado']))
        
        # Rodapé
        elementos.append(Spacer(1, 20))
        elementos.append(Paragraph(
            "Este relatório foi gerado automaticamente pelo Sistema de Gestão Contábil para Agência de Publicidade.",
            self.styles['TextoCentralizado']
        ))
        elementos.append(Paragraph(
            "© 2025 - Projeto Acadêmico da Disciplina de Contabilidade",
            self.styles['TextoCentralizado']
        ))
        
        return elementos
    
    def gerar_pdf(self, output_file=None):
        """
        Gera o relatório PDF completo.
        
        Args:
            output_file (str, optional): Caminho do arquivo PDF a ser gerado.
                                         Se None, gera um arquivo temporário.
        
        Returns:
            str: Caminho do arquivo PDF gerado ou dados em base64 se output_file for None
        """
        # Se não foi especificado um arquivo, usa um temporário
        if output_file is None:
            output_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                output_buffer, 
                pagesize=A4, 
                rightMargin=72, 
                leftMargin=72,
                topMargin=72, 
                bottomMargin=72
            )
        else:
            doc = SimpleDocTemplate(
                output_file, 
                pagesize=A4, 
                rightMargin=72, 
                leftMargin=72,
                topMargin=72, 
                bottomMargin=72
            )
        
        # Lista de elementos do relatório
        elementos = []
        
        # PÁGINA 1: Cabeçalho e métricas principais
        elementos.extend(self.gerar_cabecalho())
        elementos.extend(self.gerar_metricas_principais())
        elementos.append(PageBreak())
        
        # PÁGINA 2: Análise de custos e despesas
        elementos.extend(self.gerar_analise_custos())
        elementos.extend(self.gerar_analise_despesas())
        
        # PÁGINA 3: Análise temporal e considerações finais
        # *** IMPORTANTE: Removemos o PageBreak aqui para evitar a página em branco ***
        # elementos.append(PageBreak())
        
        # *** FIXAÇÃO: Solução alternativa usando conteúdo forçado na página atual ***
        # Em vez de usar PageBreak(), forçamos conteúdo na página atual
        elementos.append(Spacer(1, 0.5*inch))  # Pequeno espaço para separação visual
        elementos.append(Paragraph("", self.styles['NormalPersonalizado']))  # Elemento vazio para evitar quebra automática
        
        # Análise temporal e considerações
        elementos.extend(self.gerar_analise_temporal())
        consideracoes = self.gerar_consideracoes_finais()
        elementos.extend(consideracoes)
        
        # Gera o PDF com o callback especial que previne páginas em branco
        class AvoidBlankPages:
            def __init__(self):
                self.current_page = 0
            
            def on_page(self, canvas, doc):
                self.current_page += 1
        
        canvas_callback = AvoidBlankPages()
        doc.build(elementos, onFirstPage=canvas_callback.on_page, onLaterPages=canvas_callback.on_page)
        
        # Retorna o arquivo ou os dados do buffer
        if output_file is None:
            pdf_bytes = output_buffer.getvalue()
            output_buffer.close()
            
            # Converte para base64 para download via streamlit
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            return base64_pdf
        else:
            return output_file


def gerar_relatorio_financeiro(dados_metricas, periodo_inicio, periodo_fim, nome_arquivo=None):
    """
    Função de interface para gerar o relatório financeiro.
    
    Args:
        dados_metricas (dict): Dicionário com os dados das métricas calculadas
        periodo_inicio (date): Data de início do período analisado
        periodo_fim (date): Data de fim do período analisado
        nome_arquivo (str, optional): Nome do arquivo a ser gerado
    
    Returns:
        str: Caminho do arquivo ou base64 para download
    """
    # Se foi especificado um nome de arquivo, gera o caminho completo
    output_file = None
    if nome_arquivo:
        # Cria um diretório temporário para os relatórios se não existir
        relatorios_dir = os.path.join(tempfile.gettempdir(), 'relatorios_financeiros')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Gera o caminho completo do arquivo
        output_file = os.path.join(relatorios_dir, nome_arquivo)
    
    # Cria o gerador de relatórios
    gerador = FinancialReportGenerator(dados_metricas, periodo_inicio, periodo_fim)
    
    # Gera o relatório
    return gerador.gerar_pdf(output_file)


def criar_link_download(base64_pdf, filename="relatorio_financeiro.pdf"):
    """
    Cria um link HTML para download do PDF a partir dos dados em base64.
    
    Args:
        base64_pdf (str): Dados do PDF em base64
        filename (str): Nome do arquivo para download
    
    Returns:
        str: HTML com o link para download
    """
    href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{filename}">Clique aqui para baixar o PDF</a>'
    return href