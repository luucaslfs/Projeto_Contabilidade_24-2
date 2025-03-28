# Sistema de Gestão Contábil para Agência de Publicidade
## Guia para Apresentação do Projeto

Este documento serve como guia para a apresentação do projeto de Sistema de Gestão Contábil, desenvolvido para a disciplina de Contabilidade do curso de Sistemas de Informação. Ele detalha os conceitos contábeis implementados, as visualizações criadas e como explicar cada elemento durante a apresentação.

## Sumário

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Implementações Técnicas](#implementações-técnicas)
3. [Conceitos Contábeis Aplicados](#conceitos-contábeis-aplicados)
4. [Dashboard Financeiro](#dashboard-financeiro)
5. [Roteiro para Apresentação](#roteiro-para-apresentação)

---

## Visão Geral do Projeto

O projeto consiste em um sistema de gestão contábil para agências de publicidade, que permite:

- Importar dados financeiros de planilhas CSV
- Classificar automaticamente movimentações em categorias contábeis
- Diferenciar entre custos fixos e variáveis
- Analisar o fluxo de caixa e resultados financeiros
- Visualizar indicadores de desempenho através de dashboards

O sistema foi implementado com base nos conceitos contábeis das obras de:
- **Pereira da Silva, J.** - "Análise Financeira das Empresas" (13ª edição, Cengage Learning, 2017)
- **Martins, E.** - "Contabilidade de Custos" (11ª edição, GEN/Atlas, 2018)

---

## Implementações Técnicas

### Arquitetura do Sistema

- **Frontend/Backend**: Python com Streamlit
- **Banco de Dados**: PostgreSQL
- **ORM**: SQLAlchemy
- **Visualizações**: Plotly
- **Containerização**: Docker

### Principais Melhorias Implementadas

1. **Tratamento Avançado de Dados**
   - Conversão de tipos de dados (datas, valores monetários)
   - Classificação automática de naturezas contábeis
   - Identificação de custos fixos e variáveis
   - Extração de informações adicionais dos históricos

2. **Modelo de Dados Expandido**
   - Categorização contábil mais granular
   - Novos campos para análise de custos
   - Campos para entidades relacionadas e documentos

3. **Interface de Importação Aprimorada**
   - Validação de dados de entrada
   - Prévia dos dados antes da importação
   - Resumo dos dados já importados

4. **Dashboard Financeiro Otimizado**
   - Múltiplas visualizações de dados
   - Filtros por período, filial e categoria
   - Divisão em abas para diferentes análises

---

## Conceitos Contábeis Aplicados

### Baseados em Pereira da Silva (2017)

1. **Análise Vertical**
   - Representação proporcional de receitas e despesas
   - Identificação dos componentes com maior impacto no resultado

2. **Indicadores Financeiros**
   - Margem Líquida: percentual da receita que se converte em lucro
   - EBITDA: resultado operacional antes de juros, impostos, depreciação e amortização
   - Indicadores de Liquidez: capacidade de honrar compromissos financeiros

3. **Fluxo de Caixa**
   - Monitoramento de entradas e saídas
   - Projeção de saldo acumulado
   - Análise de sazonalidade

### Baseados em Martins (2018)

1. **Classificação de Custos**
   - **Custos Fixos**: independem do volume de atividade (aluguel, salários administrativos)
   - **Custos Variáveis**: relacionados diretamente ao volume de serviços prestados

2. **Índice de Fixação de Despesas**
   - Proporção de custos fixos em relação ao total
   - Indicador de rigidez operacional

3. **Análise de Ponto de Equilíbrio**
   - Receita necessária para cobrir todos os custos
   - Margem de contribuição para cobrir custos fixos

---

## Dashboard Financeiro

O dashboard foi organizado em quatro abas, cada uma com visualizações específicas relacionadas aos conceitos contábeis estudados:

### 1. Visão Geral

**Indicadores do Período**
- Receitas Totais
- Despesas Totais
- Resultado do Período
- Custos Fixos e Variáveis
- Índice de Fixação de Despesas

**Indicadores Mensais**
- Gráfico que combina receitas, despesas e margem (%)
- Aplicação do conceito de Margem de Pereira da Silva (2017)

**Distribuição por Categorias**
- Gráficos de pizza mostrando a composição de receitas e despesas
- Análise visual baseada na classificação contábil

### 2. Análise Detalhada

**Análise por Filial**
- Comparativo de desempenho entre filiais
- Entradas, saídas e resultado por unidade de negócio

**Custos Fixos vs. Variáveis**
- Evolução mensal dos custos por natureza
- Percentual de custos fixos ao longo do tempo
- Implementação direta dos conceitos de Martins (2018)

**Sazonalidade**
- Padrões recorrentes de receitas e despesas por mês
- Suporte para planejamento financeiro

### 3. Fluxo de Caixa

**Fluxo de Caixa Mensal**
- Entradas e saídas por mês
- Saldo mensal e acumulado
- Visualização para análise de liquidez

**Timeline de Movimentações**
- Visão cronológica detalhada
- Tamanho dos pontos proporcional aos valores
- Análise da evolução do saldo ao longo do tempo

**Movimentações Recentes**
- Tabela detalhada com as últimas transações

### 4. Detalhamento por Categoria

**Treemap de Receitas e Despesas**
- Visualização hierárquica por categoria e natureza
- Análise proporcional dos valores
- Identificação rápida dos principais componentes do resultado

---

## Roteiro para Apresentação

### 1. Introdução (2-3 minutos)

- Apresente o objetivo do sistema: gestão contábil para agências de publicidade
- Mencione as obras de referência (Pereira da Silva e Martins)
- Destaque que o sistema permite importação de dados reais e visualizações avançadas

### 2. Importação e Tratamento de Dados (3-4 minutos)

- Demonstre a tela de importação de CSV
- Explique como o sistema categoriza automaticamente as despesas
- Mostre como distingue custos fixos e variáveis (conceito de Martins)

### 3. Dashboard Financeiro (10-15 minutos)

**Aba Visão Geral:**
- Explique os indicadores principais:
  - "A Margem Líquida de x% significa que para cada R$100 de receita, R$x se converte em lucro"
  - "O Índice de Fixação de Despesas de y% indica que a empresa tem uma estrutura de custos relativamente rígida/flexível"

- Ao mostrar a distribuição por categorias, destaque:
  - "Esta visualização implementa o conceito de Análise Vertical de Pereira da Silva, mostrando a proporção de cada componente no total"

**Aba Análise Detalhada:**
- Ao mostrar a análise de custos fixos vs. variáveis:
  - "Segundo Martins (2018), esta classificação é fundamental para decisões gerenciais, pois custos fixos permanecem independentemente do volume de serviços"
  - "O alto percentual de custos fixos (acima de 70%) indica menor flexibilidade operacional e maior risco em períodos de baixa receita"

- Na análise de sazonalidade:
  - "Esta visualização permite identificar padrões recorrentes ao longo do ano, essencial para o planejamento financeiro da agência"

**Aba Fluxo de Caixa:**
- Ao apresentar o fluxo de caixa:
  - "O saldo acumulado positivo/negativo indica a capacidade da empresa de honrar seus compromissos financeiros"
  - "Esta análise é crucial para a liquidez, conforme destaca Pereira da Silva"

**Aba Detalhamento por Categoria:**
- Ao mostrar os treemaps:
  - "Esta visualização hierárquica permite identificar rapidamente quais categorias e naturezas específicas têm maior impacto no resultado"
  - "Por exemplo, podemos ver que a categoria X representa Y% das despesas totais"

### 4. Conclusão (2-3 minutos)

- Ressalte como o sistema integra teoria contábil e prática gerencial
- Destaque os principais benefícios para a gestão da agência:
  - Visibilidade sobre a estrutura de custos
  - Monitoramento de fluxo de caixa
  - Análise de rentabilidade
- Mencione possíveis evoluções futuras do sistema

---

## Conceitos-Chave para Destacar

Durante a apresentação, certifique-se de enfatizar estes conceitos fundamentais:

### De Pereira da Silva (2017):

1. **Análise Vertical**: Representação proporcional dos componentes financeiros em relação a um total (ex: cada despesa como percentual da receita total).

2. **Margem Líquida**: Indicador que mostra quanto da receita se converte efetivamente em lucro após todas as despesas.

3. **Liquidez**: Capacidade da empresa de honrar seus compromissos financeiros no curto prazo, visualizada através do fluxo de caixa.

### De Martins (2018):

1. **Custos Fixos vs. Variáveis**: Distinção fundamental entre custos que independem do volume de serviços (fixos) e aqueles diretamente relacionados ao volume (variáveis).

2. **Índice de Fixação**: Percentual de custos fixos em relação ao total, indicando o grau de rigidez da estrutura de custos da empresa.

3. **Estrutura de Custos**: Composição dos custos da empresa e seu impacto nas decisões gerenciais e na rentabilidade do negócio.

---

## Observações Finais

Este guia oferece uma estrutura para a apresentação do projeto, destacando os conceitos contábeis incorporados ao sistema. Adapte o conteúdo conforme necessário, enfatizando os aspectos mais relevantes para o contexto específico da disciplina de Contabilidade.

Lembre-se de que o objetivo principal é demonstrar como os conceitos teóricos de Pereira da Silva e Martins foram traduzidos em funcionalidades práticas no sistema, proporcionando ferramentas de análise financeira para a gestão de agências de publicidade.