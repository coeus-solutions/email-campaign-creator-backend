from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from datetime import datetime
from config.supabase import supabase
from models.campaign import CampaignDB, CampaignCreate, CampaignStatus
from services.email_service import email_service
from .auth import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=CampaignDB)
async def create_campaign(campaign: CampaignCreate, current_user: str = Depends(get_current_user)):
    try:
        # Validate product exists
        product = supabase.table('products').select("*").eq('id', campaign.product_id).execute()
        if not product.data:
            raise HTTPException(status_code=404, detail="Product not found")

        # Validate prospects exist
        prospects = supabase.table('prospects').select("*").in_('id', campaign.prospect_ids).execute()
        if len(prospects.data) != len(campaign.prospect_ids):
            raise HTTPException(status_code=404, detail="Some prospects not found")

        now = datetime.utcnow().isoformat()
        result = supabase.table('campaigns').insert({
            "name": campaign.name,
            "subject": campaign.subject,
            "content": campaign.content,
            "product_id": campaign.product_id,
            "prospect_ids": campaign.prospect_ids,
            "status": CampaignStatus.DRAFT,
            "created_by": current_user,
            "created_at": now,
            "updated_at": now,
            "total_prospects": len(campaign.prospect_ids),
            "sent_count": 0,
            "failed_count": 0
        }).execute()

        return result.data[0]
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[CampaignDB])
async def list_campaigns(current_user: str = Depends(get_current_user)):
    try:
        result = supabase.table('campaigns').select("*").eq('created_by', current_user).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{campaign_id}", response_model=CampaignDB)
async def get_campaign(campaign_id: str, current_user: str = Depends(get_current_user)):
    try:
        result = supabase.table('campaigns').select("*").eq('id', campaign_id).eq('created_by', current_user).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return result.data[0]
    except Exception as e:
        logger.error(f"Error getting campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def send_campaign_emails(campaign_id: str, current_user: str):
    try:
        # Get campaign details
        campaign = supabase.table('campaigns').select("*").eq('id', campaign_id).single().execute()
        if not campaign.data:
            logger.error(f"Campaign {campaign_id} not found")
            return

        # Update campaign status to running
        supabase.table('campaigns').update({
            "status": CampaignStatus.RUNNING,
            "started_at": datetime.utcnow().isoformat()
        }).eq('id', campaign_id).execute()

        # Get product details
        product = supabase.table('products').select("*").eq('id', campaign.data['product_id']).single().execute()
        if not product.data:
            logger.error(f"Product not found for campaign {campaign_id}")
            supabase.table('campaigns').update({
                "status": CampaignStatus.FAILED,
                "completed_at": datetime.utcnow().isoformat()
            }).eq('id', campaign_id).execute()
            return

        # Get prospects
        prospects = supabase.table('prospects').select("*").in_('id', campaign.data['prospect_ids']).execute()
        if not prospects.data:
            logger.error(f"No prospects found for campaign {campaign_id}")
            supabase.table('campaigns').update({
                "status": CampaignStatus.FAILED,
                "completed_at": datetime.utcnow().isoformat()
            }).eq('id', campaign_id).execute()
            return

        # Prepare recipients list with template variables
        recipients = [{
            'email': prospect['email'],
            'prospect_name': prospect['full_name'],
            'product_name': product.data['name']
        } for prospect in prospects.data]

        # Send emails using bulk send
        successful_emails, failed_emails = email_service.send_bulk_emails(
            recipients=recipients,
            subject=campaign.data['subject'],
            content_template=campaign.data['content']
        )

        # Update campaign status
        supabase.table('campaigns').update({
            "status": CampaignStatus.COMPLETED if not failed_emails else CampaignStatus.COMPLETED,
            "completed_at": datetime.utcnow().isoformat(),
            "sent_count": len(successful_emails),
            "failed_count": len(failed_emails)
        }).eq('id', campaign_id).execute()

        # Log results
        logger.info(f"Campaign {campaign_id} completed: {len(successful_emails)} sent, {len(failed_emails)} failed")

    except Exception as e:
        logger.error(f"Error processing campaign {campaign_id}: {str(e)}")
        # Update campaign status to failed
        supabase.table('campaigns').update({
            "status": CampaignStatus.FAILED,
            "completed_at": datetime.utcnow().isoformat()
        }).eq('id', campaign_id).execute()

@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: str, background_tasks: BackgroundTasks, current_user: str = Depends(get_current_user)):
    try:
        # Check if campaign exists and belongs to user
        campaign = supabase.table('campaigns').select("*").eq('id', campaign_id).eq('created_by', current_user).single().execute()
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign can be started
        if campaign.data['status'] not in [CampaignStatus.DRAFT, CampaignStatus.FAILED]:
            raise HTTPException(status_code=400, detail="Campaign cannot be started")

        # Add email sending task to background tasks
        background_tasks.add_task(send_campaign_emails, campaign_id, current_user)

        return {"message": "Campaign started successfully"}
    except Exception as e:
        logger.error(f"Error starting campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{campaign_id}/retry")
async def retry_campaign(campaign_id: str, background_tasks: BackgroundTasks, current_user: str = Depends(get_current_user)):
    try:
        # Check if campaign exists and belongs to user
        campaign = supabase.table('campaigns').select("*").eq('id', campaign_id).eq('created_by', current_user).single().execute()
        if not campaign.data:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign can be retried (must be completed with failed emails)
        if campaign.data['status'] != CampaignStatus.COMPLETED or campaign.data['failed_count'] == 0:
            raise HTTPException(status_code=400, detail="Campaign cannot be retried")

        # Reset campaign status for retry
        supabase.table('campaigns').update({
            "status": CampaignStatus.RUNNING,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "sent_count": campaign.data['sent_count'],  # Keep existing successful sends
            "failed_count": 0  # Reset failed count
        }).eq('id', campaign_id).execute()

        # Add email sending task to background tasks
        background_tasks.add_task(send_campaign_emails, campaign_id, current_user)

        return {"message": "Campaign retry initiated successfully"}
    except Exception as e:
        logger.error(f"Error retrying campaign: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 