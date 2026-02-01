import jwt
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config import settings
from app.database import accounts, account_details, account_gamification
from app.utils.helpers import generate_referral_code
import logging

logger = logging.getLogger(__name__)

class TelegramAuthService:
    """Service for Telegram WebApp authentication"""
    
    @staticmethod
    def verify_telegram_data(init_data: str) -> Dict[str, Any]:
        """Verify Telegram WebApp init data using HMAC-SHA256"""
        try:
            params = dict(pair.split('=', 1) for pair in init_data.split('&'))
            received_hash = params.pop('hash', None)
            if not received_hash:
                raise ValueError("Hash missing from init data")
            
            auth_date = int(params.get('auth_date', 0))
            if abs(datetime.utcnow().timestamp() - auth_date) > 86400:
                raise ValueError("Auth date is too old")
            
            data_check_items = [f"{k}={v}" for k, v in sorted(params.items())]
            data_check_string = '\n'.join(data_check_items)
            
            secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
            expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(received_hash, expected_hash):
                raise ValueError("Invalid hash")
            
            return params
            
        except Exception as e:
            logger.error(f"Telegram auth verification failed: {str(e)}")
            raise ValueError(f"Invalid Telegram data: {str(e)}")
    
    @staticmethod
    async def find_or_create_user(telegram_data: Dict[str, Any], referral_code: Optional[str] = None) -> Dict[str, Any]:
        """Find existing user or create new one from Telegram data"""
        import json
        
        user_data = json.loads(telegram_data.get('user', '{}'))
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            raise ValueError("Telegram ID not found")
        
        existing_detail = await account_details.find_one({"source_type": "telegram", "source_id": str(telegram_id)})
        
        if existing_detail:
            account = await accounts.find_one({"_id": existing_detail["account_id"]})
            return account
        
        username = user_data.get('username', f"user_{telegram_id}")
        first_name = user_data.get('first_name', 'User')
        last_name = user_data.get('last_name')
        photo_url = user_data.get('photo_url')
        
        referrer_id = None
        if referral_code:
            referrer = await accounts.find_one({"referral_code": referral_code})
            if referrer:
                referrer_id = str(referrer["_id"])
        
        account_doc = {
            "username": username,
            "password": "",
            "referral_code": generate_referral_code(),
            "referral_account_id": referrer_id,
            "status": "active",
            "created_at": datetime.utcnow(),
            "created_by": 1
        }
        
        account_result = await accounts.insert_one(account_doc)
        account_id = str(account_result.inserted_id)
        
        detail_doc = {
            "account_id": account_id,
            "first_name": first_name,
            "last_name": last_name,
            "source_type": "telegram",
            "source_id": str(telegram_id),
            "photo_url": photo_url,
            "created_at": datetime.utcnow(),
            "created_by": 1
        }
        await account_details.insert_one(detail_doc)
        
        gamification_doc = {
            "account_id": account_id,
            "xp": 0,
            "level": 1,
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
            "tasks_completed": 0,
            "total_earnings": 0.0,
            "created_at": datetime.utcnow()
        }
        await account_gamification.insert_one(gamification_doc)
        
        account = await accounts.find_one({"_id": account_id})
        logger.info(f"Created new user: {username} (Telegram ID: {telegram_id})")
        
        return account
    
    @staticmethod
    def generate_jwt(account_id: str) -> tuple:
        """Generate JWT access token"""
        expires_at = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        payload = {
            'sub': account_id,
            'exp': expires_at,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        
        return token, expires_at
