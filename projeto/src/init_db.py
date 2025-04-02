import os
import sys

# Adiciona o diretório atual ao path para poder importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, test_connection, IS_SQLITE
from models import Base, Cliente, Servico, Despesa, Fatura, StatusServico
from sqlalchemy import text

def init_db():
    """Inicializa o banco de dados criando todas as tabelas definidas nos modelos"""
    print("Iniciando criação das tabelas no banco de dados...")
    
    # Testa a conexão com o banco
    if not test_connection():
        print("Não foi possível conectar ao banco de dados!")
        return False
    
    try:
        # Cria todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")
        
        # Verifica se as tabelas foram criadas
        with engine.connect() as conn:
            # Lista as tabelas no banco
            if IS_SQLITE:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            else:
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
            tables = [row[0] for row in result]
            print(f"Tabelas existentes no banco: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False

def insert_sample_data():
    """Insere dados de exemplo no banco para testes"""
    from database import get_db
    from datetime import date, timedelta
    
    db = get_db()
    try:
        # Verifica se já existem dados
        clientes = db.query(Cliente).all()
        if clientes:
            print(f"Já existem {len(clientes)} clientes no banco. Pulando inserção de dados de exemplo.")
            return True
        
        # Cria clientes de exemplo
        cliente1 = Cliente(
            nome="Empresa ABC Ltda", 
            email="contato@empresaabc.com", 
            telefone="(11) 3333-4444",
            data_cadastro=date.today()
        )
        
        cliente2 = Cliente(
            nome="Comércio XYZ S.A.", 
            email="financeiro@comercioxyz.com", 
            telefone="(21) 2222-3333",
            data_cadastro=date.today() - timedelta(days=15)
        )
        
        # Adiciona os clientes ao banco
        db.add(cliente1)
        db.add(cliente2)
        db.commit()
        
        print(f"Clientes criados com IDs: {cliente1.id}, {cliente2.id}")
        
        # Cria serviços de exemplo
        servico1 = Servico(
            cliente_id=cliente1.id,
            descricao="Campanha de Marketing Digital",
            valor_mensal=3500.00,
            horas_mensais=40,
            data_inicio=date.today() - timedelta(days=30),
            status=StatusServico.ATIVO
        )
        
        servico2 = Servico(
            cliente_id=cliente2.id,
            descricao="Gestão de Redes Sociais",
            valor_mensal=2800.00,
            horas_mensais=30,
            data_inicio=date.today() - timedelta(days=45),
            status=StatusServico.ATIVO
        )
        
        # Adiciona os serviços ao banco
        db.add(servico1)
        db.add(servico2)
        db.commit()
        
        print(f"Serviços criados com IDs: {servico1.id}, {servico2.id}")
        
        # Cria algumas despesas de exemplo
        despesas = [
            Despesa(
                descricao="Aluguel",
                valor=3000.00,
                data_despesa=date.today().replace(day=5),
                categoria="Aluguel",
                observacao="Aluguel do escritório"
            ),
            Despesa(
                descricao="Energia Elétrica",
                valor=450.00,
                data_despesa=date.today().replace(day=10),
                categoria="Energia Elétrica",
                observacao="Conta de luz"
            ),
            Despesa(
                descricao="Internet",
                valor=250.00,
                data_despesa=date.today().replace(day=15),
                categoria="Telefone/Internet",
                observacao="Conta de internet"
            )
        ]
        
        # Adiciona as despesas ao banco
        for despesa in despesas:
            db.add(despesa)
        db.commit()
        
        # Cria algumas faturas de exemplo
        fatura1 = Fatura(
            cliente_id=cliente1.id,
            servico_id=servico1.id,
            mes_referencia=date.today().replace(day=1) - timedelta(days=30),
            data_emissao=date.today().replace(day=5),
            valor=servico1.valor_mensal,
            status="pendente"
        )
        
        fatura2 = Fatura(
            cliente_id=cliente2.id,
            servico_id=servico2.id,
            mes_referencia=date.today().replace(day=1) - timedelta(days=30),
            data_emissao=date.today().replace(day=5),
            valor=servico2.valor_mensal,
            status="pago"
        )
        
        # Adiciona as faturas (com tratamento de erro individual)
        try:
            db.add(fatura1)
            db.flush()
            print("Fatura 1 adicionada com sucesso.")
        except Exception as e:
            db.rollback()
            print(f"Erro ao adicionar fatura 1: {e}")
        
        try:
            db.add(fatura2)
            db.commit()
            print("Fatura 2 adicionada com sucesso.")
        except Exception as e:
            db.rollback()
            print(f"Erro ao adicionar fatura 2: {e}")
            return False
        
        print("Dados de exemplo inseridos com sucesso!")
        return True
    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados de exemplo: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if init_db():
        print("Banco de dados inicializado com sucesso!")
        
        # Em modo interativo, pergunta ao usuário se deseja inserir dados
        try:
            resposta = input("Deseja inserir dados de exemplo para testes? (s/n): ")
            if resposta.lower() == 's':
                if insert_sample_data():
                    print("Dados de exemplo inseridos com sucesso!")
                else:
                    print("Erro ao inserir dados de exemplo.")
        except EOFError:
            # Em caso de execução não-interativa, não insere dados
            print("Modo não-interativo detectado. Nenhum dado de exemplo será inserido.")
    else:
        print("Erro ao inicializar o banco de dados.")