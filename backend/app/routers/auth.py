from fastapi import APIRouter, HTTPException, status
from app.models.schemas import TelegramAuthRequest, AuthResponse, UserSession
from app.services.telegram_auth_service import TelegramAuthService
from app.database import accounts, account_details, emails
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(request: TelegramAuthRequest):
    """Authenticate user with Telegram WebApp init data"""
    try:
        telegram_data = TelegramAuthService.verify_telegram_data(request.init_data)
        referral_code = telegram_data.get('start_param')
        account = await TelegramAuthService.find_or_create_user(telegram_data, referral_code)
        account_id = str(account['_id'])
        details = await account_details.find_one({"account_id": account_id})
        primary_email = await emails.find_one({"account_id": account_id, "is_primary": True})
        
        email_status = "none"
        if primary_email:
            email_status = "verified" if primary_email.get("status") == "verified" else "pending"
        
        access_token, expires_at = TelegramAuthService.generate_jwt(account_id)
        
        user_session = UserSession(
            id=account_id,
            telegram_id=int(details.get('source_id', 0)),
            username=account.get('username'),
            first_name=details.get('first_name', 'User'),
            last_name=details.get('last_name'),
            photo_url=details.get('photo_url'),
            email=primary_email['email'] if primary_email else None,
            email_verification_status=email_status,
            referral_code=account.get('referral_code', ''),
            referred_by=account.get('referral_account_id'),
            created_at=account.get('created_at')
        )
        
        return AuthResponse(access_token=access_token, expires_at=expires_at, user=user_session)
        
    except ValueError as e:
        logger.error(f"Telegram auth failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in telegram auth: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed")
