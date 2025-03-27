# Criar arquivo src/import_excel.py
import pandas as pd
from sqlalchemy.orm import Session
from models import PlanoContas, MovimentacaoBancaria
from database import get_db
import os
import streamlit as st

def importar_plano_contas(arquivo_excel):
    """Importa o plano de contas da planilha para o banco de dados"""
    try:
        # Lê o plano de contas da planilha
        df = pd.read_excel(arquivo_excel, sheet_name="Plano de Contas")
        df['Codigo'] = df['Codigo'].astype(str).str.replace('.0', '')
        
        # Lê as movimentações para extrair naturezas adicionais
        mov_df = pd.read_excel(arquivo_excel, sheet_name="Movimentacao Bancaria")
        
        # Processa naturezas das movimentações para adicionar ao plano
        naturezas_df = mov_df[['Natureza', 'Nome Natureza']].drop_duplicates().dropna()
        naturezas_df['Natureza'] = naturezas_df['Natureza'].astype(str).str.replace('.0', '')
        
        # Cria um dicionário para armazenar todos os códigos e descrições
        codigos_plano = {}
        
        # Adiciona códigos do plano de contas ao dicionário
        for _, row in df.iterrows():
            codigos_plano[row['Codigo']] = row['Descricao']
        
        # Adiciona códigos das naturezas das movimentações 
        # (apenas se ainda não existirem no dicionário)
        for _, row in naturezas_df.iterrows():
            if row['Natureza'] not in codigos_plano:
                codigos_plano[row['Natureza']] = row['Nome Natureza']
        
        # Limpa as tabelas - IMPORTANTE: primeiro movimentações, depois plano de contas
        db = get_db()
        db.query(MovimentacaoBancaria).delete()  # Primeiro limpa movimentações
        db.query(PlanoContas).delete()           # Depois limpa plano de contas
        
        # Insere todos os registros do dicionário
        for codigo, descricao in codigos_plano.items():
            conta = PlanoContas(
                codigo=codigo,
                descricao=descricao
            )
            db.add(conta)
        
        db.commit()
        return True, f"Importados {len(codigos_plano)} registros do plano de contas com sucesso!"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return False, f"Erro ao importar plano de contas: {str(e)}"
    
    finally:
        if 'db' in locals():
            db.close()

def importar_movimentacoes(arquivo_excel):
    """Importa as movimentações bancárias da planilha para o banco de dados"""
    try:
        # Lê as movimentações da planilha
        df = pd.read_excel(arquivo_excel, sheet_name="Movimentacao Bancaria")
        
        # Converte as colunas para os tipos adequados
        df['Entrada'] = pd.to_numeric(df['Entrada'], errors='coerce')
        df['Saida'] = pd.to_numeric(df['Saida'], errors='coerce')
        
        # Converte Natureza para string e remove .0
        df['Natureza'] = df['Natureza'].astype(str).str.replace('.0', '')
        df['Natureza'] = df['Natureza'].replace('nan', '')
        
        # Remove linhas com datas inválidas ou nulas e outras colunas essenciais
        df = df.dropna(subset=['Data'])  # Remove linhas com data nula
        
        # Garante que filial, banco, agencia, conta e documento são strings
        colunas_para_string = ['Filial Orig', 'Banco', 'Agencia', 'Conta Banco', 'Documento', 'Historico']
        for col in colunas_para_string:
            df[col] = df[col].astype(str).replace('nan', '')
        
        # Remove linhas de totalização ou resumo (geralmente têm valores mas não têm natureza)
        df = df[df['Natureza'] != '']
        
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
                
                mov = MovimentacaoBancaria(
                    filial=str(row['Filial Orig']).replace('.0', ''),
                    data=pd.to_datetime(row['Data']).date(),
                    banco=str(row['Banco']),
                    agencia=str(row['Agencia']).replace('.0', ''),
                    conta=str(row['Conta Banco']).replace('.0', ''),
                    natureza=str(row['Natureza']),
                    documento=str(row['Documento']),
                    entrada=row['Entrada'] if not pd.isna(row['Entrada']) else None,
                    saida=row['Saida'] if not pd.isna(row['Saida']) else None,
                    historico=str(row['Historico'])
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