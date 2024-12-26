from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class CampaignBase(BaseModel):
    name: str
    subject: str
    content: str
    product_id: str
    prospect_ids: List[str]

class CampaignCreate(CampaignBase):
    pass

class CampaignDB(CampaignBase):
    id: str
    status: CampaignStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_prospects: int
    sent_count: int = 0
    failed_count: int = 0

    class Config:
        from_attributes = True

class CampaignResponse(CampaignDB):
    pass

# For backward compatibility
Campaign = CampaignDB 