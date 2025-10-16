import os
import sys
import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv() 

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if not DB_HOST or not DB_USER or DB_PASSWORD is None or not DB_NAME:
    print(" Verifique seu .env (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).", file=sys.stderr)
    sys.exit(1)

@contextmanager
def connect(db=None):
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=db,
        port=3306,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def exec_sql(conn, sql, label):
    with conn.cursor() as c:
        print(f"> {label}")
        c.execute(sql)

def exec_sql_params(conn, sql, params, label):
    with conn.cursor() as c:
        print(f"> {label}")
        c.execute(sql, params)

def fetch_one(conn, sql, params=None):
    with conn.cursor() as c:
        c.execute(sql, params or ())
        return c.fetchone()

def fetch_value(conn, sql, params=None):
    row = fetch_one(conn, sql, params)
    return row[0] if row else None

def seed(conn):
    print("\n Iniciando SEED idempotente (somente categorias e produtos)...")

    categories = ["Eletrônicos", "Livros", "Roupas"]
    for cat in categories:
        exists = fetch_value(conn, "SELECT id FROM categories WHERE name=%s", (cat,))
        if not exists:
            exec_sql_params(conn,
                "INSERT INTO categories (name) VALUES (%s)",
                (cat,),
                f"Inserindo categoria {cat}"
            )

    def get_category_id(name):
        cid = fetch_value(conn, "SELECT id FROM categories WHERE name=%s", (name,))
        if cid is None:
            raise RuntimeError(f"Categoria '{name}' não encontrada (seed).")
        return cid

    prods = [
        ("Mouse",   "Mouse óptico",        59.90, 100, "Eletrônicos"),
        ("Teclado", "Teclado mecânico",   199.90,  50, "Eletrônicos"),
        ("Livro A", "Romance",             39.90, 200, "Livros"),
    ]
    for name, desc, price, stock, cat_name in prods:
        cid = get_category_id(cat_name)
        exists = fetch_value(conn, "SELECT id FROM products WHERE name=%s AND category_id=%s", (name, cid))
        if not exists:
            exec_sql_params(conn, """
                INSERT INTO products (name, description, price, stock, category_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, desc, price, stock, cid), f"Inserindo produto {name}")

    print(" Seed concluído com sucesso (categorias e produtos).")

def main():
    print(f"Conectando em {DB_HOST} como {DB_USER}…")
    with connect() as conn:
        exec_sql(conn, f"""
            CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """, f"Criando database `{DB_NAME}` (se não existir)")

    print(f"Conectando no DB `{DB_NAME}`…")
    with connect(db=DB_NAME) as conn:
        exec_sql(conn, """
        CREATE TABLE IF NOT EXISTS users (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          email VARCHAR(120) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """, "Tabela users")

        exec_sql(conn, """
        CREATE TABLE IF NOT EXISTS categories (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL UNIQUE
        ) ENGINE=InnoDB;
        """, "Tabela categories")

        exec_sql(conn, """
        CREATE TABLE IF NOT EXISTS products (
          id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(150) NOT NULL,
          description TEXT,
          price DECIMAL(10,2) NOT NULL,
          stock INT NOT NULL DEFAULT 0,
          category_id INT NOT NULL,
          CONSTRAINT chk_price_nonneg CHECK (price >= 0),
          CONSTRAINT chk_stock_nonneg CHECK (stock >= 0),
          INDEX idx_products_category (category_id),
          FOREIGN KEY (category_id) REFERENCES categories(id)
        ) ENGINE=InnoDB;
        """, "Tabela products")

        exec_sql(conn, """
        CREATE TABLE IF NOT EXISTS orders (
          id INT AUTO_INCREMENT PRIMARY KEY,
          user_id INT NOT NULL,
          status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
          total DECIMAL(10,2) NOT NULL DEFAULT 0,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT chk_status CHECK (status IN ('PENDING','PAID','CANCELLED')),
          INDEX idx_orders_user (user_id),
          FOREIGN KEY (user_id) REFERENCES users(id)
        ) ENGINE=InnoDB;
        """, "Tabela orders")

        exec_sql(conn, """
        CREATE TABLE IF NOT EXISTS order_items (
          id INT AUTO_INCREMENT PRIMARY KEY,
          order_id INT NOT NULL,
          product_id INT NOT NULL,
          quantity INT NOT NULL,
          unit_price DECIMAL(10,2) NOT NULL,
          CONSTRAINT chk_qty_pos CHECK (quantity > 0),
          INDEX idx_items_order (order_id),
          INDEX idx_items_product (product_id),
          UNIQUE(order_id, product_id),
          FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
          FOREIGN KEY (product_id) REFERENCES products(id)
        ) ENGINE=InnoDB;
        """, "Tabela order_items")

        exec_sql(conn, "DROP PROCEDURE IF EXISTS sp_recalc_order_total;", "Drop SP sp_recalc_order_total")
        exec_sql(conn, """
        CREATE PROCEDURE sp_recalc_order_total (IN p_order_id INT)
        BEGIN
          UPDATE orders o
          SET o.total = (
            SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
            FROM order_items oi
            WHERE oi.order_id = p_order_id
          )
          WHERE o.id = p_order_id;
        END;
        """, "Create SP sp_recalc_order_total")

        exec_sql(conn, "DROP PROCEDURE IF EXISTS sp_top_categories_sales;", "Drop SP sp_top_categories_sales")
        exec_sql(conn, """
        CREATE PROCEDURE sp_top_categories_sales (IN p_limit INT)
        BEGIN
          SELECT c.id, c.name,
                 COALESCE(SUM(oi.quantity * oi.unit_price),0) AS revenue,
                 COUNT(DISTINCT o.id) AS orders_count
          FROM categories c
          LEFT JOIN products p ON p.category_id = c.id
          LEFT JOIN order_items oi ON oi.product_id = p.id
          LEFT JOIN orders o ON o.id = oi.order_id
          GROUP BY c.id, c.name
          ORDER BY revenue DESC
          LIMIT p_limit;
        END;
        """, "Create SP sp_top_categories_sales")

        seed(conn)

    print("\n Pronto! Database, estrutura e seed criados.")
    print(f"- DB: {DB_NAME}")
    print("- Tabelas: users, categories, products, orders, order_items")
    print("- Procedures: sp_recalc_order_total, sp_top_categories_sales")
    print("- Seed: categorias e produtos")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f" Erro: {e}", file=sys.stderr)
        sys.exit(1)
