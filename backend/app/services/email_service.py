from datetime import datetime, timedelta
from typing import Optional
from app.database import emails, isps, confirmation_emails
from app.utils.helpers import generate_verification_code
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for email operations"""
    
    @staticmethod
    async def detect_isp(email_domain: str) -> Optional[str]:
        """Detect ISP from email domain"""
        isp_doc = await isps.find_one({"domains": email_domain})
        return str(isp_doc["_id"]) if isp_doc else None
    
    @staticmethod
    async def send_verification_email(email_id: str, email_address: str) -> dict:
        """Send verification code (mocked for now)"""
        code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # Store verification code
        confirmation_doc = {
            "email_id": email_id,
            "code": code,
            "ip_address": "0.0.0.0",  # Would be real IP in production
            "confirmed_at": None,
            "created_at": datetime.utcnow()
        }
        
        await confirmation_emails.insert_one(confirmation_doc)
        
        # Mock email send
        logger.info(f"[MOCK EMAIL] Verification code for {email_address}: {code}")
        
        # Update email status
        await emails.update_one(
            {"_id": email_id},
            {"$set": {"status": "verification_sent", "updated_at": datetime.utcnow()}}
        )
        
        return {
            "sent": True,
            "expires_at": expires_at,
            "code": code  # Only in mock mode
        }
    
    @staticmethod
    async def verify_code(email_id: str, code: str) -> bool:
        """Verify email verification code"""
        # Find the most recent verification code
        confirmation = await confirmation_emails.find_one(
            {"email_id": email_id, "code": code},
            sort=[("created_at", -1)]
        )
        
        if not confirmation:
            return False
        
        # Check if already confirmed
        if confirmation.get("confirmed_at"):
            return True
        
        # Check expiration (30 minutes)
        created_at = confirmation["created_at"]
        if datetime.utcnow() - created_at > timedelta(minutes=30):
            return False
        
        # Mark as confirmed
        await confirmation_emails.update_one(
            {"_id": confirmation["_id"]},
            {"$set": {"confirmed_at": datetime.utcnow()}}
        )
        
        # Update email status
        await emails.update_one(
            {"_id": email_id},
            {"$set": {"status": "verified", "updated_at": datetime.utcnow()}}
        )
        
        return True
