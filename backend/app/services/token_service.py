import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import settings
from app.utils.helpers import generate_nonce, hash_string
import logging

logger = logging.getLogger(__name__)

class TokenService:
    """Service for generating and verifying tracking tokens"""
    
    @staticmethod
    def generate_tracking_token(email_task_id: str, event_type: str, destination_url: str = None) -> Dict[str, str]:
        """Generate a signed tracking token for email opens/clicks"""
        nonce = generate_nonce()
        expires_at = datetime.utcnow() + timedelta(days=settings.TOKEN_EXPIRATION_DAYS)
        
        payload = {
            'et_id': email_task_id,
            'evt': event_type,
            'exp': int(expires_at.timestamp()),
            'n': nonce
        }
        
        # For clicks, add destination hash
        if event_type == 'click' and destination_url:
            dst_hash = hash_string(destination_url)[:8]
            payload['dst'] = dst_hash
        
        token = jwt.encode(payload, settings.TOKEN_SIGNING_KEY, algorithm='HS256')
        
        return {
            'token': token,
            'nonce': nonce
        }
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode tracking token"""
        try:
            payload = jwt.decode(token, settings.TOKEN_SIGNING_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def get_open_pixel_url(email_task_id: str) -> str:
        """Generate open pixel URL"""
        token_data = TokenService.generate_tracking_token(email_task_id, 'open')
        return f"/o/{token_data['token']}.png"
    
    @staticmethod
    def get_click_url(email_task_id: str, destination_url: str) -> str:
        """Generate click redirect URL"""
        token_data = TokenService.generate_tracking_token(email_task_id, 'click', destination_url)
        return f"/c/{token_data['token']}?u={destination_url}"
