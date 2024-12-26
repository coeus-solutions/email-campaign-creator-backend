from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class TimestampedModel(BaseModel):
    created_at: datetime
    updated_at: datetime

class UserOwnedModel(TimestampedModel):
    created_by: str 