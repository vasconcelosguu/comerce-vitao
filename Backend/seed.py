# seed.py
from random import choice, randint
from datetime import datetime

from sqlalchemy import text

from app.database import SessionLocal
from app.models import User, Category, Product, Order, OrderItem

db = SessionLocal()

print()
print("=== Iniciando SEED do Banco ===")
print()

try:
    # ----------------------------
    # 1. Criar usuarios (se nao existirem)
    # ----------------------------
    users_data = [
        ("Ana Gomes", "ana@example.com"),
        ("Bruno Henrique", "bruno@example.com"),
        ("Carla Cabelo", "carla@example.com"),
        ("Daniel Souza", "daniel@example.com"),
        ("Fernanda Lima", "fernanda@example.com"),
    ]

    users = []
    for name, email in users_data:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users.append(existing)
        else:
            user = User(name=name, email=email, password_hash="$pbkdf2-sha256$29000$SmntvdcaA4AQorS29r7Xug$9PLuesX.rRQ.Fv9ACme2MbhtXYgnrTl/X6Z8AXpqnxs")
            db.add(user)
            users.append(user)

    db.commit()
    print("Usuarios criados ou reaproveitados.")

    # ----------------------------
    # 2. Criar categorias
    # ----------------------------
    categories_data = [
        "Eletronicos",
        "Informatica",
        "Celulares",
        "Acessorios",
        "Perifericos",
    ]

    categories = []
    for name in categories_data:
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            categories.append(existing)
        else:
            cat = Category(name=name)
            db.add(cat)
            categories.append(cat)

    db.commit()
    print("Categorias criadas ou reaproveitadas.")

    # ----------------------------
    # 3. Criar produtos
    # ----------------------------
    products_data = [
        ("Mouse Gamer", 89.90, 10),
        ("Teclado Mecanico", 249.90, 5),
        ("Monitor 24", 899.90, 4),
        ("Headset USB", 129.90, 12),
        ("Webcam HD", 79.90, 15),
        ("Notebook i5", 2999.90, 3),
        ("Cabo HDMI", 29.90, 20),
        ("Pen Drive 64GB", 39.90, 25),
        ("SSD 480GB", 199.90, 8),
        ("Mousepad Grande", 49.90, 30),
    ]

    products = []
    for name, price, stock in products_data:
        existing = db.query(Product).filter(Product.name == name).first()
        if existing:
            products.append(existing)
        else:
            prod = Product(
                name=name,
                description="Produto: " + name,
                price=price,
                stock=stock,
                category_id=choice(categories).id,
            )
            db.add(prod)
            products.append(prod)

    db.commit()
    print("Produtos criados ou reaproveitados.")

    # Recarregar listas para garantir IDs atualizados
    users = db.query(User).all()
    categories = db.query(Category).all()
    products = db.query(Product).all()

    # ----------------------------
    # 4. Criar pedidos
    # ----------------------------
    print("Criando pedidos...")

    for _ in range(10):
        user = choice(users)
        order = Order(
            user_id=user.id,
            status="PENDING",
            total=0,
            created_at=datetime.utcnow(),
        )
        db.add(order)
        db.flush()  # garante que order.id exista

        # cada pedido tem entre 1 e 3 itens
        num_items = randint(1, 3)
        selected_products = [choice(products) for _ in range(num_items)]

        for prod in selected_products:
            if prod.stock <= 0:
                continue

            qty = randint(1, 3)
            if qty > prod.stock:
                qty = prod.stock

            if qty <= 0:
                continue

            item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=qty,
                unit_price=prod.price,
            )
            db.add(item)

            prod.stock -= qty  # baixa estoque

        # recalcular total automaticamente via procedure (MySQL)
        db.execute(text("CALL sp_recalc_order_total(:oid)"), {"oid": order.id})

    db.commit()

    print("Pedidos criados.")
    print()
    print("=== SEED FINALIZADO COM SUCESSO ===")
    print()

except Exception as e:
    db.rollback()
    print("Erro durante o seed:", e)

finally:
    db.close()
