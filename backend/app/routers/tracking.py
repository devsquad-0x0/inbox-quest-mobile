from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from app.services.token_service import TokenService
from app.database import tracking_events, email_tasks
from datetime import datetime
from PIL import Image
import io
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

def create_transparent_pixel():
    """Create a 1x1 transparent PNG"""
    img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@router.get("/o/{token}.png")
async def track_open(token: str, request: Request):
    """Track email open via pixel"""
    try:
        # Verify token
        payload = TokenService.verify_token(token.replace('.png', ''))
        
        email_task_id = payload.get('et_id')
        nonce = payload.get('n')
        
        if not email_task_id or not nonce:
            logger.warning("Invalid token payload")
            return StreamingResponse(create_transparent_pixel(), media_type="image/png")
        
        # Get client IP
        client_ip = request.client.host
        
        # Check for duplicate (dedupe by email_task_id + nonce + IP within 60 seconds)
        recent_event = await tracking_events.find_one({
            "email_task_id": email_task_id,
            "event_type": "open",
            "token_nonce": nonce,
            "ip_address": client_ip,
            "created_at": {"$gte": datetime.utcnow() - timedelta(seconds=60)}
        })
        
        if recent_event:
            logger.info(f"Duplicate open event detected for task {email_task_id}")
            return StreamingResponse(create_transparent_pixel(), media_type="image/png")
        
        # Log tracking event
        event_doc = {
            "email_task_id": email_task_id,
            "event_type": "open",
            "token_nonce": nonce,
            "ip_address": client_ip,
            "user_agent_id": None,
            "asn_id": None,
            "is_valid": True,
            "rejection_reason": None,
            "processed_at": None,
            "reward_credited": False,
            "created_at": datetime.utcnow()
        }
        
        await tracking_events.insert_one(event_doc)
        
        # Update email_task status
        email_task = await email_tasks.find_one({"_id": email_task_id})
        if email_task and email_task.get("status") == "pending":
            await email_tasks.update_one(
                {"_id": email_task_id},
                {"$set": {"status": "opened", "updated_at": datetime.utcnow()}}
            )
            logger.info(f"Email task {email_task_id} marked as opened")
        
        return StreamingResponse(create_transparent_pixel(), media_type="image/png")
        
    except Exception as e:
        logger.error(f"Error tracking open: {str(e)}")
        return StreamingResponse(create_transparent_pixel(), media_type="image/png")

@router.get("/c/{token}")
async def track_click(token: str, u: str, request: Request):
    """Track click and redirect"""
    try:
        # Verify token
        payload = TokenService.verify_token(token)
        
        email_task_id = payload.get('et_id')
        nonce = payload.get('n')
        
        if not email_task_id or not nonce:
            logger.warning("Invalid token payload")
            return RedirectResponse(url="https://inboxquest.com")
        
        # Get client IP
        client_ip = request.client.host
        
        # Check for duplicate (dedupe by email_task_id + nonce within 5 minutes)
        recent_event = await tracking_events.find_one({
            "email_task_id": email_task_id,
            "event_type": "click",
            "token_nonce": nonce,
            "created_at": {"$gte": datetime.utcnow() - timedelta(minutes=5)}
        })
        
        if not recent_event:
            # Log tracking event
            event_doc = {
                "email_task_id": email_task_id,
                "event_type": "click",
                "token_nonce": nonce,
                "ip_address": client_ip,
                "user_agent_id": None,
                "asn_id": None,
                "is_valid": True,
                "rejection_reason": None,
                "processed_at": None,
                "reward_credited": False,
                "created_at": datetime.utcnow()
            }
            
            await tracking_events.insert_one(event_doc)
            
            # Update email_task status to completed
            email_task = await email_tasks.find_one({"_id": email_task_id})
            if email_task and email_task.get("status") in ["pending", "opened"]:
                await email_tasks.update_one(
                    {"_id": email_task_id},
                    {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
                )
                logger.info(f"Email task {email_task_id} marked as completed")
                
                # Award reward (simplified - in production would use queue)
                from app.services.wallet_service import WalletService
                from app.database import tasks
                
                task = await tasks.find_one({"_id": email_task.get("task_id")})
                if task:
                    reward = float(task.get("cost", 0))
                    await WalletService.credit(
                        account_id=email_task.get("account_id"),
                        amount=reward,
                        entry_type="task_reward",
                        reference_type="email_task",
                        reference_id=email_task_id,
                        description=f"Task reward - {task.get('code', '')}",
                        idempotency_key=f"task_reward_{email_task_id}"
                    )
                    
                    await email_tasks.update_one(
                        {"_id": email_task_id},
                        {"$set": {"status": "rewarded"}}
                    )
        
        # Redirect to destination
        return RedirectResponse(url=u if u else "https://inboxquest.com")
        
    except Exception as e:
        logger.error(f"Error tracking click: {str(e)}")
        return RedirectResponse(url="https://inboxquest.com")
