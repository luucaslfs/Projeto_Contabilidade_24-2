from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import date
import enum

Base = declarative_base()

class StatusServico(enum.Enum):
    ATIVO = "ativo"
    PAUSADO = "pausado"
    CANCELADO = "cancelado"

class Cliente(Base):
    __tablename__ = 'clientes'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    telefone = Column(String(20))
    data_cadastro = Column(Date, default=date.today)
    
    # Relacionamentos
    servicos = relationship("Servico", back_populates="cliente")
    faturas = relationship("Fatura", back_populates="cliente")

class Servico(Base):
    __tablename__ = 'servicos'
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    descricao = Column(String(200), nullable=False)
    valor_mensal = Column(Float, nullable=False)
    horas_mensais = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False)
    status = Column(Enum(StatusServico), default=StatusServico.ATIVO)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="servicos")
    faturas = relationship("Fatura", back_populates="servico")

class Despesa(Base):
    __tablename__ = 'despesas'
    
    id = Column(Integer, primary_key=True)
    descricao = Column(String(200), nullable=False)
    valor = Column(Float, nullable=False)
    data_despesa = Column(Date, nullable=False)
    categoria = Column(String(50), nullable=False)  # Aluguel, Luz, Internet, etc
    observacao = Column(String(500))
    # Campos adicionais
    tipo = Column(String(50), default='Variável')  # Fixo ou Variável
    fornecedor = Column(String(100))
    documento_ref = Column(String(50))  # Referência a NF, recibo, etc

class Fatura(Base):
    __tablename__ = 'faturas'
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    servico_id = Column(Integer, ForeignKey('servicos.id'), nullable=False)
    mes_referencia = Column(Date, nullable=False)  # Mês do serviço prestado
    data_emissao = Column(Date, nullable=False)    # Data de emissão (mês seguinte)
    valor = Column(Float, nullable=False)
    status = Column(String(20), default='pendente')  # pendente, pago, cancelado
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="faturas")
    servico = relationship("Servico", back_populates="faturas")

class PlanoContas(Base):
    __tablename__ = 'plano_contas'
    
    codigo = Column(String(20), primary_key=True)
    descricao = Column(String(200), nullable=False)
    # Campos adicionais
    categoria = Column(String(100))  # Categorização contábil principal
    subcategoria = Column(String(100))  # Subcategorização opcional
    
class MovimentacaoBancaria(Base):
    __tablename__ = 'movimentacoes'
    
    id = Column(Integer, primary_key=True)
    filial = Column(String(10), nullable=False)
    data = Column(Date, nullable=False)
    banco = Column(String(20))
    agencia = Column(String(20))
    conta = Column(String(20))
    natureza = Column(String(20), ForeignKey('plano_contas.codigo'))
    nome_natureza = Column(String(200))  # Nome da natureza para facilitar consultas
    documento = Column(String(50))
    entrada = Column(Float, nullable=True)
    saida = Column(Float, nullable=True)
    historico = Column(Text)
    # Campos adicionais para análise
    categoria = Column(String(100))  # Categoria contábil (Receitas, Despesas, etc)
    tipo_custo = Column(String(50))  # Fixo ou Variável
    entidade = Column(String(100))  # Cliente ou Fornecedor extraído do histórico
    documento_ref = Column(String(50))  # Referência a NF ou documento extraído do histórico
    
    # Relacionamento
    conta_natureza = relationship("PlanoContas")