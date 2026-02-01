from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.schemas import CampaignListResponse, Campaign, SubscribeResponse
from app.middleware.auth_middleware import get_current_user
from app.database import campaigns, email_campaigns, emails, email_tasks
from bson import ObjectId
import logging

from datetime import datetime
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    status_filter: str = Query("active", alias="status"),
    subscribed: bool = Query(None),
    current_user=Depends(get_current_user)
):
    """List all campaigns with subscription status"""
    account_id = str(current_user["_id"])
    
    # Get user's primary email
    primary_email = await emails.find_one({"account_id": account_id, "is_primary": True})
    email_id = str(primary_email["_id"]) if primary_email else None
    
    # Get all active campaigns
    query = {"status": status_filter}
    campaign_list = await campaigns.find(query).to_list(100)
    
    result = []
    for camp in campaign_list:
        campaign_id = str(camp["_id"])
        
        # Check subscription
        is_subscribed = False
        if email_id:
            subscription = await email_campaigns.find_one({
                "email_id": email_id,
                "campaign_id": campaign_id
            })
            is_subscribed = subscription is not None
        
        # Count active tasks for this campaign
        active_task_count = 0
        if email_id and is_subscribed:
            active_task_count = await email_tasks.count_documents({
                "email_id": email_id,
                "status": {"$in": ["pending", "opened", "clicked"]}
            })
        
        # Filter by subscription if requested
        if subscribed is not None and is_subscribed != subscribed:
            continue
        
        result.append(Campaign(
            id=campaign_id,
            code=camp.get("code", ""),
            name=camp.get("name", ""),
            description=camp.get("description"),
            vertical_name=camp.get("vertical_name"),
            is_subscribed=is_subscribed,
            active_task_count=active_task_count,
            status=camp.get("status", "active")
        ))
    
    return CampaignListResponse(campaigns=result)

@router.post("/{campaign_id}/subscribe", response_model=SubscribeResponse)
async def subscribe_to_campaign(campaign_id: str, current_user=Depends(get_current_user)):
    """Subscribe to a campaign"""
    account_id = str(current_user["_id"])
    
    # Check email verification
    primary_email = await emails.find_one({
        "account_id": account_id,
        "is_primary": True,
        "status": "verified"
    })
    
    if not primary_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must be verified before subscribing to campaigns"
        )
    
    email_id = str(primary_email["_id"])
    
    # Check if campaign exists
    campaign = await campaigns.find_one({"_id": campaign_id})
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    
    # Check if already subscribed
    existing = await email_campaigns.find_one({
        "email_id": email_id,
        "campaign_id": campaign_id
    })
    
    if existing:
        return SubscribeResponse(subscribed=True)
    
    # Create subscription
    await email_campaigns.insert_one({
        "email_id": email_id,
        "campaign_id": campaign_id,
        "created_at": datetime.utcnow(),
        "created_by": 1
    })
    
    logger.info(f"User {account_id} subscribed to campaign {campaign_id}")
    
    return SubscribeResponse(subscribed=True)

@router.delete("/{campaign_id}/subscribe", response_model=SubscribeResponse)
async def unsubscribe_from_campaign(campaign_id: str, current_user=Depends(get_current_user)):
    """Unsubscribe from a campaign"""
    account_id = str(current_user["_id"])
    
    primary_email = await emails.find_one({"account_id": account_id, "is_primary": True})
    if not primary_email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    
    email_id = str(primary_email["_id"])
    
    # Delete subscription
    result = await email_campaigns.delete_one({
        "email_id": email_id,
        "campaign_id": campaign_id
    })
    
    return SubscribeResponse(subscribed=False)
