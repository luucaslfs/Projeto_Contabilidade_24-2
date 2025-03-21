import streamlit as st
import pandas as pd
from datetime import date
import sys
import os

# Adiciona o diretório src ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, test_connection
from models import Cliente

def load_clientes():
    """Carrega todos os clientes do banco de dados"""
    db = get_db()
    try:
        clientes = db.query(Cliente).all()
        return clientes
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")
        return []
    finally:
        db.close()

def salvar_cliente(nome, email, telefone):
    """Salva um novo cliente no banco de dados"""
    if not nome or not email:
        st.error("Nome e email são obrigatórios!")
        return False
    
    db = get_db()
    try:
        # Verifica se já existe um cliente com este email
        cliente_existente = db.query(Cliente).filter(Cliente.email == email).first()
        if cliente_existente:
            st.error(f"Já existe um cliente cadastrado com o email {email}")
            return False
        
        # Cria o novo cliente
        novo_cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            data_cadastro=date.today()
        )
        
        # Adiciona e salva no banco
        db.add(novo_cliente)
        db.commit()
        
        st.success(f"Cliente {nome} cadastrado com sucesso!")
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Erro ao salvar cliente: {e}")
        return False
    finally:
        db.close()

def atualizar_cliente(cliente_id, nome, email, telefone):
    """Atualiza um cliente existente no banco de dados"""
    if not nome or not email:
        st.error("Nome e email são obrigatórios!")
        return False
    
    db = get_db()
    try:
        # Busca o cliente pelo ID
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        
        if not cliente:
            st.error(f"Cliente com ID {cliente_id} não encontrado!")
            return False
        
        # Verifica se o email já está em uso por outro cliente
        if email != cliente.email:
            cliente_existente = db.query(Cliente).filter(Cliente.email == email).first()
            if cliente_existente:
                st.error(f"Já existe outro cliente cadastrado com o email {email}")
                return False
        
        # Atualiza os dados
        cliente.nome = nome
        cliente.email = email
        cliente.telefone = telefone
        
        # Salva as alterações
        db.commit()
        
        st.success(f"Cliente {nome} atualizado com sucesso!")
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Erro ao atualizar cliente: {e}")
        return False
    finally:
        db.close()

def excluir_cliente(cliente_id):
    """Exclui um cliente do banco de dados"""
    db = get_db()
    try:
        # Busca o cliente pelo ID
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        
        if not cliente:
            st.error(f"Cliente com ID {cliente_id} não encontrado!")
            return False
        
        # Exclui o cliente
        db.delete(cliente)
        db.commit()
        
        st.success(f"Cliente {cliente.nome} excluído com sucesso!")
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Erro ao excluir cliente: {e}")
        return False
    finally:
        db.close()

def main():
    st.title("Cadastro de Clientes")
    
    # Adiciona um diagnóstico detalhado da conexão com o banco
    st.write("### Status da Conexão")
    with st.spinner("Verificando conexão com o banco de dados..."):
        connection_result = test_connection()
    
    if connection_result:
        st.success("✅ Conexão com o banco de dados estabelecida com sucesso!")
    else:
        st.error("❌ Não foi possível conectar ao banco de dados!")
        
        # Adiciona informações adicionais para debugging
        st.warning("### Informações de Debugging")
        st.code(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Não definido')}")
        
        # Botão para reconectar
        if st.button("Tentar Conectar Novamente"):
            st.experimental_rerun()
            
        # Exibe instruções para resolver o problema
        st.info("""
        ### Possíveis soluções:
        1. Verifique se o container do banco de dados está rodando: `docker ps`
        2. Verifique os logs do container do banco: `docker logs [container_id]`
        3. Verifique se as credenciais do banco estão corretas no arquivo .env ou docker-compose.yaml
        """)
        
        return
    
    # Tabs para organizar as funcionalidades
    tab1, tab2, tab3 = st.tabs(["Cadastrar", "Listar/Editar", "Excluir"])
    
    with tab1:
        st.header("Novo Cliente")
        
        # Formulário de cadastro
        with st.form(key="cadastro_cliente"):
            nome = st.text_input("Nome completo*")
            email = st.text_input("Email*")
            telefone = st.text_input("Telefone")
            
            submit_button = st.form_submit_button(label="Cadastrar")
            if submit_button:
                salvar_cliente(nome, email, telefone)
    
    with tab2:
        st.header("Lista de Clientes")
        
        # Carrega os clientes
        clientes = load_clientes()
        
        if not clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            # Exibe os clientes em um DataFrame
            df = pd.DataFrame([
                {
                    "ID": c.id,
                    "Nome": c.nome,
                    "Email": c.email,
                    "Telefone": c.telefone,
                    "Data Cadastro": c.data_cadastro.strftime("%d/%m/%Y") if c.data_cadastro else ""
                } for c in clientes
            ])
            
            st.dataframe(df)
            
            # Formulário de edição
            st.subheader("Editar Cliente")
            
            # Seleciona o cliente a ser editado
            cliente_ids = [c.id for c in clientes]
            cliente_nomes = [c.nome for c in clientes]
            
            opcoes = [f"{id} - {nome}" for id, nome in zip(cliente_ids, cliente_nomes)]
            if opcoes:
                selecao = st.selectbox("Selecione um cliente para editar:", opcoes)
                cliente_id = int(selecao.split(" - ")[0])
                
                # Pega o cliente selecionado
                cliente_selecionado = next((c for c in clientes if c.id == cliente_id), None)
                
                if cliente_selecionado:
                    with st.form(key="editar_cliente"):
                        nome_edit = st.text_input("Nome completo*", value=cliente_selecionado.nome)
                        email_edit = st.text_input("Email*", value=cliente_selecionado.email)
                        telefone_edit = st.text_input("Telefone", value=cliente_selecionado.telefone or "")
                        
                        submit_edit = st.form_submit_button(label="Atualizar")
                        if submit_edit:
                            atualizar_cliente(cliente_id, nome_edit, email_edit, telefone_edit)
                            st.experimental_rerun()
    
    with tab3:
        st.header("Excluir Cliente")
        
        # Carrega os clientes
        clientes = load_clientes()
        
        if not clientes:
            st.info("Nenhum cliente cadastrado.")
        else:
            # Seleciona o cliente a ser excluído
            cliente_ids = [c.id for c in clientes]
            cliente_nomes = [c.nome for c in clientes]
            
            opcoes = [f"{id} - {nome}" for id, nome in zip(cliente_ids, cliente_nomes)]
            
            selecao = st.selectbox("Selecione um cliente para excluir:", opcoes)
            cliente_id = int(selecao.split(" - ")[0])
            
            if st.button("Excluir Cliente", type="primary", help="Esta ação não pode ser desfeita!"):
                # Pede confirmação
                confirmacao = st.checkbox("Confirmo que desejo excluir este cliente e todos seus dados associados")
                
                if confirmacao:
                    if excluir_cliente(cliente_id):
                        st.experimental_rerun()

if __name__ == "__main__":
    main()
