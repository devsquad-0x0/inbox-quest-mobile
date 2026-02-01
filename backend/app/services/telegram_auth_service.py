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
    \"\"\"Service for Telegram WebApp authentication\"\"\"
    
    @staticmethod
    def verify_telegram_data(init_data: str) -> Dict[str, Any]:
        \"\"\"Verify Telegram WebApp init data using HMAC-SHA256\"\"\"
        try:
            # Parse init_data query string
            params = dict(pair.split('=', 1) for pair in init_data.split('&'))
            
            # Extract hash and create data check string
            received_hash = params.pop('hash', None)
            if not received_hash:
                raise ValueError(\"Hash missing from init data\")
            
            # Check auth_date (must be within 24 hours)
            auth_date = int(params.get('auth_date', 0))
            if abs(datetime.utcnow().timestamp() - auth_date) > 86400:
                raise ValueError(\"Auth date is too old\")
            \n            # Create data check string (sorted alphabetically)
            data_check_items = [f\"{k}={v}\" for k, v in sorted(params.items())]\n            data_check_string = '\\n'.join(data_check_items)\n            \n            # Calculate HMAC-SHA256\n            secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()\n            expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()\n            \n            if not hmac.compare_digest(received_hash, expected_hash):\n                raise ValueError(\"Invalid hash\")\n            \n            return params\n            \n        except Exception as e:\n            logger.error(f\"Telegram auth verification failed: {str(e)}\")\n            raise ValueError(f\"Invalid Telegram data: {str(e)}\")\n    \n    @staticmethod\n    async def find_or_create_user(telegram_data: Dict[str, Any], referral_code: Optional[str] = None) -> Dict[str, Any]:\n        \"\"\"Find existing user or create new one from Telegram data\"\"\"\n        import json\n        \n        # Parse user data from Telegram\n        user_data = json.loads(telegram_data.get('user', '{}'))\n        telegram_id = user_data.get('id')\n        \n        if not telegram_id:\n            raise ValueError(\"Telegram ID not found\")\n        \n        # Check if user exists\n        existing_detail = await account_details.find_one({\n            \"source_type\": \"telegram\",\n            \"source_id\": str(telegram_id)\n        })\n        \n        if existing_detail:\n            # Return existing user\n            account = await accounts.find_one({\"_id\": existing_detail[\"account_id\"]})\n            return account\n        \n        # Create new user\n        username = user_data.get('username', f\"user_{telegram_id}\")\n        first_name = user_data.get('first_name', 'User')\n        last_name = user_data.get('last_name')\n        photo_url = user_data.get('photo_url')\n        \n        # Handle referral\n        referrer_id = None\n        if referral_code:\n            referrer = await accounts.find_one({\"referral_code\": referral_code})\n            if referrer:\n                referrer_id = str(referrer[\"_id\"])\n        \n        # Create account\n        account_doc = {\n            \"username\": username,\n            \"password\": \"\",  # No password for Telegram users\n            \"referral_code\": generate_referral_code(),\n            \"referral_account_id\": referrer_id,\n            \"status\": \"active\",\n            \"created_at\": datetime.utcnow(),\n            \"created_by\": 1\n        }\n        \n        account_result = await accounts.insert_one(account_doc)\n        account_id = str(account_result.inserted_id)\n        \n        # Create account details\n        detail_doc = {\n            \"account_id\": account_id,\n            \"first_name\": first_name,\n            \"last_name\": last_name,\n            \"source_type\": \"telegram\",\n            \"source_id\": str(telegram_id),\n            \"photo_url\": photo_url,\n            \"created_at\": datetime.utcnow(),\n            \"created_by\": 1\n        }\n        await account_details.insert_one(detail_doc)\n        \n        # Create gamification record\n        gamification_doc = {\n            \"account_id\": account_id,\n            \"xp\": 0,\n            \"level\": 1,\n            \"current_streak\": 0,\n            \"longest_streak\": 0,\n            \"last_activity_date\": None,\n            \"tasks_completed\": 0,\n            \"total_earnings\": 0.0,\n            \"created_at\": datetime.utcnow()\n        }\n        await account_gamification.insert_one(gamification_doc)\n        \n        # Get the created account\n        account = await accounts.find_one({\"_id\": account_id})\n        \n        logger.info(f\"Created new user: {username} (Telegram ID: {telegram_id})\")\n        \n        return account\n    \n    @staticmethod\n    def generate_jwt(account_id: str) -> tuple[str, datetime]:\n        \"\"\"Generate JWT access token\"\"\"\n        expires_at = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)\n        \n        payload = {\n            'sub': account_id,\n            'exp': expires_at,\n            'iat': datetime.utcnow()\n        }\n        \n        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)\n        \n        return token, expires_at\n