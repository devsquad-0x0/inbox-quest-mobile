from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import EmailResponse, AddEmailRequest, SendVerificationResponse, VerifyEmailRequest, VerifyEmailResponse
from app.middleware.auth_middleware import get_current_user
from app.database import emails, confirmation_emails
from app.services.email_service import EmailService
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=EmailResponse | dict)
async def get_my_email(current_user=Depends(get_current_user)):
    """Get current user's primary email status"""
    account_id = str(current_user["_id"])
    
    email = await emails.find_one({
        "account_id": account_id,
        "is_primary": True
    })
    
    if not email:
        return {"email": None, "status": "none"}
    
    # Check if verified
    confirmation = await confirmation_emails.find_one({
        "email_id": str(email["_id"]),
        "confirmed_at": {"$ne": None}
    })
    
    return EmailResponse(
        id=str(email["_id"]),
        email=email["email"],
        status=email.get("status", "pending"),
        verified_at=confirmation.get("confirmed_at") if confirmation else None
    )

@router.post("", response_model=EmailResponse)
async def add_email(request: AddEmailRequest, current_user=Depends(get_current_user)):
    """Add primary email to account"""
    account_id = str(current_user["_id"])
    
    # Check if primary email already exists
    existing = await emails.find_one({
        "account_id": account_id,
        "is_primary": True
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primary email already exists"
        )
    
    # Check if email already in use
    duplicate = await emails.find_one({"email": request.email})
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use"
        )
    
    # Detect ISP
    email_domain = request.email.split('@')[1]
    isp_id = await EmailService.detect_isp(email_domain)
    
    # Create email
    email_doc = {
        "account_id": account_id,
        "email": request.email,
        "isp_id": isp_id,
        "status": "pending",
        "is_primary": True,
        "created_at": datetime.utcnow(),
        "created_by": 1
    }
    
    result = await emails.insert_one(email_doc)
    email_id = str(result.inserted_id)
    
    return EmailResponse(
        id=email_id,
        email=request.email,
        status="pending",
        verified_at=None
    )

@router.post("/{email_id}/send-verification", response_model=SendVerificationResponse)
async def send_verification(email_id: str, current_user=Depends(get_current_user)):
    """Send verification code to email"""
    account_id = str(current_user["_id"])
    
    # Get email
    email = await emails.find_one({"_id": email_id, "account_id": account_id})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Send verification
    result = await EmailService.send_verification_email(email_id, email["email"])
    
    return SendVerificationResponse(
        sent=result["sent"],
        expires_at=result["expires_at"]
    )

@router.post("/{email_id}/verify", response_model=VerifyEmailResponse)
async def verify_email(email_id: str, request: VerifyEmailRequest, current_user=Depends(get_current_user)):
    """Verify email with code"""
    account_id = str(current_user["_id"])
    
    # Get email
    email = await emails.find_one({"_id": email_id, "account_id": account_id})
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Verify code
    verified = await EmailService.verify_code(email_id, request.code)
    
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    return VerifyEmailResponse(verified=True)
