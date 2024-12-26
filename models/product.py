from pydantic import BaseModel, UUID4
from typing import Optional
from .base import UserOwnedModel

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductDB(ProductBase, UserOwnedModel):
    id: UUID4

class ProductResponse(ProductDB):
    pass 