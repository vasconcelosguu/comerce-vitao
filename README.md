# E-commerce API – Projeto Backend Completo (FastAPI + SQLAlchemy)

## Descrição Geral

Este projeto implementa a API backend de um sistema de e-commerce, construída em Python com FastAPI e SQLAlchemy ORM.
O sistema foi desenvolvido como trabalho acadêmico para demonstrar:

- Modelagem de banco de dados relacional
- API RESTful modular e segura
- Uso de transações e regras de negócio
- Consultas SQL avançadas
- Boas práticas de arquitetura e documentação

O backend está pronto para integração com qualquer frontend (web ou mobile).

---

## Tecnologias Utilizadas

| Categoria                  | Tecnologias                                       |
|---------------------------|---------------------------------------------------|
| Linguagem                 | Python 3.11+                                      |
| Framework Web             | FastAPI                                           |
| ORM                       | SQLAlchemy                                        |
| Banco de Dados            | MySQL (produção) / SQLite (testes)               |
| Validação                 | Pydantic                                          |
| Hashing                   | Passlib (bcrypt)                                  |
| Variáveis de ambiente     | python-dotenv                                     |
| Testes                    | pytest                                            |
| Servidor local            | Uvicorn                                           |

---

## Arquitetura de Pastas

```
Backend/
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── utils.py
│
├── tests/
│   ├── conftest.py
│   ├── test_orders.py
│
├── init_db.py
├── seed.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## Modelagem de Dados

O sistema contém as seguintes entidades:

- Usuários  
- Categorias  
- Produtos  
- Pedidos  
- Itens de Pedido  

Relacionamento principal:

```
users (1) ──< orders (1) ──< order_items >── products (N) ──< categories
```

---

## Como Executar o Projeto

### 1. Criar ambiente virtual

```
python -m venv venv
```

### 2. Ativar ambiente

Windows:
```
venv\Scripts\activate
```

Linux/Mac:
```
source venv/bin/activate
```

### 3. Instalar dependências

```
pip install -r requirements.txt
```

### 4. Configurar o .env

Exemplo:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=1234
DB_NAME=ecommerce_db
```

### 5. Inicializar o banco

```
python init_db.py
python seed.py
```

### 6. Executar a API

```
uvicorn app.main:app --reload
```

Acesse:
- Swagger: http://127.0.0.1:8000/docs  
- ReDoc: http://127.0.0.1:8000/redoc  

---

## Endpoints Principais

### Usuários
- POST /users/  
- GET /users/

### Categorias
- POST /categories/  
- GET /categories/

### Produtos
- POST /products/  
- GET /products/  
- GET /products/{id}

### Pedidos
- POST /orders/  
- GET /orders/  
- POST /orders/{id}/cancel  

---

## Consultas SQL Avançadas

### Faturamento por categoria
```sql
SELECT c.name,
       SUM(oi.quantity * oi.unit_price) AS revenue
FROM categories c
JOIN products p ON p.category_id = c.id
JOIN order_items oi ON oi.product_id = p.id
GROUP BY c.name
ORDER BY revenue DESC;
```

### Usuários que mais gastaram
```sql
SELECT u.name,
       SUM(o.total) AS total_spent
FROM users u
JOIN orders o ON o.user_id = u.id
GROUP BY u.name
ORDER BY total_spent DESC;
```

### Produtos sem pedidos
```sql
SELECT p.id, p.name
FROM products p
WHERE NOT EXISTS (
    SELECT 1 FROM order_items oi WHERE oi.product_id = p.id
);
```

### Produtos com estoque baixo
```sql
SELECT p.name, p.stock,
       SUM(oi.quantity) AS sold
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id
HAVING p.stock < 10;
```

---

## Autores

| Nome | GitHub |
|------|--------|
| Felipe Piovesan | https://github.com/ffpiovesan |
| Frederico Brumatti | https://github.com/FredBrumati |
| Gustavo Vasconcelos | https://github.com/vasconcelosguu |
| Ruan Gimenes | https://github.com/Ruan-0101 |
| Vitor Zuchierri | https://github.com/VitorZuchierri |
