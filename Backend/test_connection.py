from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM products;"))
        count = result.scalar()
        print(f" Conexão OK! Tabela 'products' encontrada com {count} produtos.")
except Exception as e:
    print(" Erro ao conectar ou acessar a tabela 'products':")
    print(e)
