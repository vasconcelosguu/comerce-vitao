from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import User, Category, Product
from app.schemas import (
    UserCreate, UserOut,
    CategoryIn, CategoryOut,
    ProductIn, ProductOut
)
from app.utils import hash_password, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-commerce API - Minimal")

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

@app.get("/users/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()

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

@app.get("/categories/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()

@app.post("/products/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductIn, db: Session = Depends(get_db)):
    cat = db.get(Category, payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="Categoria inválida")
    prod = Product(**payload.dict())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

@app.get("/products/", response_model=list[ProductOut])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()