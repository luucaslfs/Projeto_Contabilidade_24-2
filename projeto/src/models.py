from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
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