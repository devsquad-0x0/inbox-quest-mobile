from datetime import datetime
from app.database import account_gamification
from app.utils.helpers import get_level_from_xp
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class GamificationService:
    """Service for gamification operations"""
    
    @staticmethod
    async def add_xp(account_id: str, xp_amount: int):
        """Add XP to account and update level"""
        gamification = await account_gamification.find_one({"account_id": account_id})
        
        if not gamification:
            logger.warning(f"Gamification record not found for account {account_id}")
            return
        
        new_xp = gamification.get("xp", 0) + xp_amount
        new_level = get_level_from_xp(new_xp, settings.LEVEL_THRESHOLDS)
        
        await account_gamification.update_one(
            {"account_id": account_id},
            {
                "$set": {
                    "xp": new_xp,
                    "level": new_level,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Added {xp_amount} XP to account {account_id}. New XP: {new_xp}, Level: {new_level}")
    
    @staticmethod
    async def increment_tasks_completed(account_id: str):
        """Increment tasks completed counter"""
        await account_gamification.update_one(
            {"account_id": account_id},
            {
                "$inc": {"tasks_completed": 1},
                "$set": {
                    "last_activity_date": datetime.utcnow().date().isoformat(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    async def update_streak(account_id: str, streak_value: int):
        """Update streak values"""
        gamification = await account_gamification.find_one({"account_id": account_id})
        
        if not gamification:
            return
        
        longest_streak = max(gamification.get("longest_streak", 0), streak_value)
        
        await account_gamification.update_one(
            {"account_id": account_id},
            {
                "$set": {
                    "current_streak": streak_value,
                    "longest_streak": longest_streak,
                    "last_activity_date": datetime.utcnow().date().isoformat(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
