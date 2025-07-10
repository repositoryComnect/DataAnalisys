import os

class Config:
    # Configurações gerais
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-aqui'
    
    # SQLite para usuários (autenticação)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    
    # PostgreSQL para dados de negócio
    SQLALCHEMY_BINDS = {
        'pg': os.environ.get('DATABASE_URL') or 'postgresql://usuario:senha@localhost/faturamento'
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações específicas do PostgreSQL
    PG_POOL_SIZE = 5
    PG_MAX_OVERFLOW = 10
    PG_POOL_RECYCLE = 3600


