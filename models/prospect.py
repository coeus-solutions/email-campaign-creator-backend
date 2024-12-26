from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, Dict, Any
from .base import UserOwnedModel

class ProspectBase(BaseModel):
    email: EmailStr
    full_name: str
    company: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class ProspectCreate(ProspectBase):
    pass

class ProspectDB(ProspectBase, UserOwnedModel):
    id: UUID4

class ProspectResponse(ProspectDB):
    pass 