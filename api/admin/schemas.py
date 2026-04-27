from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    brand: str
    category: str
    status: Optional[str] = "active"
    specs: Optional[str] = None
    warranty: Optional[str] = None
    price: int
    discount: Optional[int] = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    specs: Optional[str] = None
    warranty: Optional[str] = None
    status: Optional[str] = None


class PriceUpdate(BaseModel):
    price: Optional[int] = None
    discount: Optional[int] = None
