from fastapi import APIRouter, Depends, Query
from app.models.schemas import TaskListResponse, TaskAssignment
from app.middleware.auth_middleware import get_current_user
from app.database import email_tasks, tasks, actions, offers, campaigns, emails
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

STATUS_LABELS = {
    "pending": "Check your inbox",
    "opened": "Opened",
    "clicked": "Clicked",
    "completed": "Completed",
    "rewarded": "Completed",
    "expired": "Expired",
    "failed": "Failed"
}

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status_filter: str = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user=Depends(get_current_user)
):
    """List task assignments for current user"""
    account_id = str(current_user["_id"])
    
    # Get user's primary email
    primary_email = await emails.find_one({"account_id": account_id, "is_primary": True})
    if not primary_email:
        return TaskListResponse(tasks=[], total=0, limit=limit, offset=offset)
    
    email_id = str(primary_email["_id"])
    
    # Build query
    query = {"email_id": email_id}
    if status_filter:
        query["status"] = {"$in": status_filter.split(",")}
    
    # Get total count
    total = await email_tasks.count_documents(query)
    
    # Get tasks
    email_task_list = await email_tasks.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    result = []
    for et in email_task_list:
        # Get task details
        task = await tasks.find_one({"_id": et["task_id"]})
        if not task:
            continue
        
        # Get action
        action = await actions.find_one({"_id": task["action_id"]})
        
        # Get offer and campaign
        offer = await offers.find_one({"_id": task["offer_id"]})
        campaign = await campaigns.find_one({"_id": offer["campaign_id"]}) if offer else None
        
        task_status = et.get("status", "pending")
        
        result.append(TaskAssignment(
            id=str(et["_id"]),
            task_code=task.get("code", ""),
            campaign_name=campaign.get("name", "") if campaign else "",
            campaign_code=campaign.get("code", "") if campaign else "",
            action_type=action.get("slug", "") if action else "",
            action_number=task.get("action_number", 1),
            reward=float(task.get("cost", 0)),
            xp_reward=25,  # Fixed XP per task
            status=task_status,
            status_label=STATUS_LABELS.get(task_status, task_status),
            instructions=f"Check your inbox for email from {campaign.get('name', 'campaign')}" if campaign else "Check your inbox",
            email_subject=None,
            expires_at=et.get("expires_at"),
            completed_at=et.get("updated_at") if task_status in ["completed", "rewarded"] else None,
            created_at=et.get("created_at", datetime.utcnow())
        ))
    
    return TaskListResponse(tasks=result, total=total, limit=limit, offset=offset)
