from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from .base import TimestampedModel

class CampaignProspectBase(BaseModel):
    campaign_id: UUID4
    prospect_id: UUID4
    status: str
    email_content: str
    email_status: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

class CampaignProspectCreate(CampaignProspectBase):
    pass

class CampaignProspectDB(CampaignProspectBase, TimestampedModel):
    id: UUID4

class CampaignProspectResponse(CampaignProspectDB):
    pass

class CampaignProspectStatus:
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    OPENED = "opened"
    CLICKED = "clicked"

class EmailStatus:
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed" 