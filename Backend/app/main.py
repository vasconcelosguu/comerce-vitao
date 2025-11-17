from typing import List
import os

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import User, Category, Product, Order, OrderItem
from app.schemas import (
    UserCreate, UserOut,
    CategoryIn, CategoryOut,
    ProductIn, ProductOut,
    OrderCreate, OrderOut, OrderItemOut,
)
from app.utils import hash_password

if os.getenv("APP_ENV", "dev") == "dev":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-commerce API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.asc()).all()


@app.post("/categories/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryIn, db: Session = Depends(get_db)):
    exists = db.query(Category).filter(Category.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Categoria já existe")
    cat = Category(name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@app.get("/categories/", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name.asc()).all()


@app.post("/products/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductIn, db: Session = Depends(get_db)):
    cat = db.get(Category, payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="Categoria inválida")

    prod = Product(
        name=payload.name,
        description=payload.description or "",
        price=payload.price,
        stock=payload.stock,
        category_id=payload.category_id,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@app.get("/products/", response_model=List[ProductOut])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.get(Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return prod

@app.post("/orders/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Usuário inválido")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Pedido precisa de ao menos um item")

    try:
        order = Order(user_id=payload.user_id, status="PENDING", total=0)
        db.add(order)
        db.flush() 

        running_total = 0.0

        for it in payload.items:
            product = db.get(Product, it.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Produto {it.product_id} não encontrado")

            if product.stock < it.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estoque insuficiente para o produto {product.id}",
                )

            product.stock -= it.quantity
            unit_price = float(product.price)
            running_total += unit_price * it.quantity

            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=it.quantity,
                unit_price=unit_price,
            ))

        order.total = running_total
        db.add(order)

        db.commit()  
        db.refresh(order)

        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        return OrderOut(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total=float(order.total),
            items=[
                OrderItemOut(
                    product_id=it.product_id,
                    quantity=it.quantity,
                    unit_price=float(it.unit_price),
                ) for it in items
            ],
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao criar pedido: {e}")

@app.get("/orders/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.id.desc()).all()
    result: List[OrderOut] = []
    for o in orders:
        items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        result.append(
            OrderOut(
                id=o.id,
                user_id=o.user_id,
                status=o.status,
                total=float(o.total),
                items=[
                    OrderItemOut(
                        product_id=it.product_id,
                        quantity=it.quantity,
                        unit_price=float(it.unit_price),
                    )
                    for it in items
                ],
            )
        )
    return result

@app.get("/reports/top-categories")
def report_top_categories(limit: int = Query(5, gt=0, le=100), db: Session = Depends(get_db)):
    sql = text("""
        SELECT
            c.id AS category_id,
            c.name AS category_name,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS revenue,
            COUNT(DISTINCT o.id) AS orders_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        LEFT JOIN order_items oi ON oi.product_id = p.id
        LEFT JOIN orders o ON o.id = oi.order_id
        GROUP BY c.id, c.name
        ORDER BY revenue DESC
        LIMIT :limit_val
    """)
    rows = db.execute(sql, {"limit_val": limit}).mappings().all()
    return [dict(r) for r in rows]

@app.get("/reports/top-users")
def report_top_users(limit: int = Query(5, gt=0, le=100), db: Session = Depends(get_db)):
    sql = text("""
        SELECT
            u.id   AS user_id,
            u.name AS user_name,
            u.email AS user_email,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS spent,
            COUNT(DISTINCT o.id) AS orders_count
        FROM users u
        LEFT JOIN orders o ON o.user_id = u.id AND o.status <> 'CANCELLED'
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY u.id, u.name, u.email
        ORDER BY spent DESC
        LIMIT :limit_val
    """)
    rows = db.execute(sql, {"limit_val": limit}).mappings().all()
    return [dict(r) for r in rows]

@app.get("/reports/low-stock")
def report_low_stock(threshold: int = Query(5, ge=0), db: Session = Depends(get_db)):
    sql = text("""
        SELECT id, name, stock
        FROM products
        WHERE stock <= :thr
        ORDER BY stock ASC, id ASC
    """)
    rows = db.execute(sql, {"thr": threshold}).mappings().all()
    return [dict(r) for r in rows]

@app.get("/reports/products-without-orders")
def report_products_without_orders(db: Session = Depends(get_db)):
    sql = text("""
        SELECT p.id, p.name, p.stock
        FROM products p
        WHERE NOT EXISTS (
            SELECT 1
            FROM order_items oi
            WHERE oi.product_id = p.id
        )
        ORDER BY p.id ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [dict(r) for r in rows]
