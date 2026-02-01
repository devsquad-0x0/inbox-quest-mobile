from fastapi import APIRouter, Depends
from app.models.schemas import AchievementListResponse, Achievement
from app.middleware.auth_middleware import get_current_user
from app.database import achievements, account_achievements, account_gamification, accounts
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=AchievementListResponse)
async def list_achievements(current_user=Depends(get_current_user)):
    """List all achievements with user progress"""
    account_id = str(current_user["_id"])
    
    # Get all active achievements
    achievement_list = await achievements.find({"status": "active"}).to_list(100)
    
    # Get gamification data
    gamification = await account_gamification.find_one({"account_id": account_id})
    
    # Get referral count
    referral_count = await accounts.count_documents({"referral_account_id": account_id})
    
    result = []
    for ach in achievement_list:
        achievement_id = str(ach["_id"])
        
        # Get user progress for this achievement
        user_achievement = await account_achievements.find_one({
            "account_id": account_id,
            "achievement_id": achievement_id
        })
        
        # Calculate progress based on requirement type
        requirement_type = ach.get("requirement_type", "")
        requirement_value = ach.get("requirement_value", 0)
        current_value = 0
        
        if gamification:
            if requirement_type == "tasks_completed":
                current_value = gamification.get("tasks_completed", 0)
            elif requirement_type == "earnings_total":
                current_value = int(gamification.get("total_earnings", 0))
            elif requirement_type == "streak_days":
                current_value = gamification.get("current_streak", 0)
            elif requirement_type == "level_reached":
                current_value = gamification.get("level", 1)
        
        if requirement_type == "referrals_count":
            current_value = referral_count
        
        progress = min(current_value, requirement_value)
        progress_percent = int((progress / requirement_value) * 100) if requirement_value > 0 else 0
        
        is_unlocked = user_achievement and user_achievement.get("unlocked_at") is not None
        
        result.append(Achievement(
            id=achievement_id,
            code=ach.get("code", ""),
            name=ach.get("name", ""),
            description=ach.get("description", ""),
            category=ach.get("category", ""),
            icon=ach.get("icon", "trophy"),
            requirement_value=requirement_value,
            xp_reward=ach.get("xp_reward", 0),
            cash_reward=float(ach.get("cash_reward", 0)),
            is_unlocked=is_unlocked,
            unlocked_at=user_achievement.get("unlocked_at") if user_achievement else None,
            progress=progress,
            progress_percent=min(progress_percent, 100)
        ))
    
    return AchievementListResponse(achievements=result)
