from pydantic import BaseModel
from typing import Optional


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
