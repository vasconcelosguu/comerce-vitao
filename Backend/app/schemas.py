from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr

class CategoryIn(BaseModel):
    name: str = Field(..., min_length=1)

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class ProductIn(BaseModel):
    name: str
    description: Optional[str] = ""
    price: float
    stock: int
    category_id: int

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = ""
    price: float
    stock: int
    category_id: int

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemIn]

class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    quantity: int
    unit_price: float

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    status: str
    total: float
    items: List[OrderItemOut]