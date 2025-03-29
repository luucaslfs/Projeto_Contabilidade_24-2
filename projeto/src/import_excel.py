import pandas as pd
import numpy as np
from datetime import datetime
import re
from sqlalchemy.orm import Session
from models import PlanoContas, MovimentacaoBancaria
from database import get_db
import os
import streamlit as st

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

def extrair_info_historico(historico):
    """Extrai informações adicionais do campo histórico"""
    if pd.isna(historico) or not isinstance(historico, str):
        return {}
    
    info = {}
    
    # Tenta identificar fornecedor/cliente
    if ":" in historico:
        partes = historico.split(":")
        if len(partes) > 1:
            info['entidade'] = partes[0].strip()
    
    # Tenta identificar NF ou documento
    padrao_nf = r'(nf|nota fiscal|doc)[\s:\-]*(\d+)'
    match_nf = re.search(padrao_nf, historico.lower())
    if match_nf:
        info['documento_ref'] = match_nf.group(2)
    
    return info

def importar_plano_contas(arquivo_csv):
    """Importa o plano de contas da planilha CSV para o banco de dados"""
    try:
        # Lê o arquivo CSV
        df = pd.read_csv(arquivo_csv, encoding='utf-8')
        
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

def importar_movimentacoes(arquivo_csv):
    """Importa as movimentações bancárias do CSV para o banco de dados"""
    try:
        # Lê o arquivo CSV
        df = pd.read_csv(arquivo_csv, encoding='utf-8')
        
        # Converte tipos de dados
        df['Data'] = df['Data'].apply(converter_data)
        df['Entrada'] = df['Entrada'].apply(limpar_valor_monetario)
        df['Saida'] = df['Saida'].apply(limpar_valor_monetario)
        
        # Converte códigos para string
        for col in ['Filial Orig', 'Agencia', 'Conta Banco', 'Natureza']:
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
                
                # Extrai informações do histórico
                info_extra = extrair_info_historico(row['Historico'])
                
                mov = MovimentacaoBancaria(
                    filial=str(row['Filial Orig']),
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
                    tipo_custo=str(row.get('Tipo', 'Não classificado')),
                    entidade=info_extra.get('entidade', ''),
                    documento_ref=info_extra.get('documento_ref', '')
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