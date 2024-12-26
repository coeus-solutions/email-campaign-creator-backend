from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional
from .base import TimestampedModel

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserDB(UserBase, TimestampedModel):
    id: UUID4
    password_hash: str

class UserResponse(UserBase, TimestampedModel):
    id: UUID4 