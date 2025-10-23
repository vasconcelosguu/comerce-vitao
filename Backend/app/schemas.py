from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length = 1)
    email: str = EmailStr
    password: str = Field(..., min_length = 6)

class UserOut(BaseModel):
    id: int 
    name: str
    class Config:
        from_attributes = True

class CategoryIn(BaseModel):
    name: str = Field(..., min_length = 1)

class CategoryOut(BaseModel):
    id: int 
    name: str
    class Config:
        from_attributes = True

class ProductIn(BaseModel):
    name: str 
    description: Optional[str] = ""
    price: float
    stock: int
    category_id: int

class ProductOut(BaseModel):
    id: int 
    name: str
    class Config:
        from_attributes = True