from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import UserGamification, DailyBonusResponse
from app.middleware.auth_middleware import get_current_user
from app.database import account_gamification, daily_bonus_claims
from app.services.wallet_service import WalletService
from app.services.gamification_service import GamificationService
from app.utils.helpers import get_level_from_xp, calculate_xp_progress
from app.config import settings
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=UserGamification)
async def get_gamification(current_user=Depends(get_current_user)):
    """Get user gamification stats"""
    account_id = str(current_user["_id"])
    
    gamification = await account_gamification.find_one({"account_id": account_id})
    if not gamification:
        # Create if not exists
        gamification = {
            "account_id": account_id,
            "xp": 0,
            "level": 1,
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
            "tasks_completed": 0,
            "total_earnings": 0.0
        }
        await account_gamification.insert_one(gamification)
    
    xp = gamification.get("xp", 0)
    level = get_level_from_xp(xp, settings.LEVEL_THRESHOLDS)
    level_name = settings.LEVEL_NAMES[level - 1] if level <= len(settings.LEVEL_NAMES) else "Max Level"
    
    xp_to_next, progress_percent = calculate_xp_progress(xp, level, settings.LEVEL_THRESHOLDS)
    
    # Check daily bonus availability
    today = date.today()
    today_claim = await daily_bonus_claims.find_one({
        "account_id": account_id,
        "claim_date": today.isoformat()
    })
    daily_bonus_available = today_claim is None
    
    # Calculate streak day (1-7)
    current_streak = gamification.get("current_streak", 0)
    streak_day = (current_streak % 7) + 1 if current_streak > 0 else 1
    
    return UserGamification(
        xp=xp,
        level=level,
        level_name=level_name,
        xp_to_next_level=xp_to_next,
        xp_progress=progress_percent,
        current_streak=gamification.get("current_streak", 0),
        longest_streak=gamification.get("longest_streak", 0),
        tasks_completed=gamification.get("tasks_completed", 0),
        daily_bonus_available=daily_bonus_available,
        daily_bonus_streak_day=streak_day
    )

@router.post("/daily-bonus", response_model=DailyBonusResponse)
async def claim_daily_bonus(current_user=Depends(get_current_user)):
    """Claim daily bonus"""
    account_id = str(current_user["_id"])
    
    today = date.today()
    
    # Check if already claimed today
    existing_claim = await daily_bonus_claims.find_one({
        "account_id": account_id,
        "claim_date": today.isoformat()
    })
    
    if existing_claim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily bonus already claimed today"
        )
    
    # Get gamification data
    gamification = await account_gamification.find_one({"account_id": account_id})
    if not gamification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gamification data not found")
    
    # Calculate streak
    last_activity_date = gamification.get("last_activity_date")
    current_streak = gamification.get("current_streak", 0)
    
    if last_activity_date:
        last_date = datetime.fromisoformat(last_activity_date).date()
        days_diff = (today - last_date).days
        
        if days_diff == 1:
            # Continue streak
            current_streak += 1
        elif days_diff > 1:
            # Broken streak
            current_streak = 1
    else:
        current_streak = 1
    
    # Get streak day (1-7)
    streak_day = ((current_streak - 1) % 7) + 1
    
    # Get bonus amounts
    bonus_amount, xp_amount = settings.DAILY_BONUS_SCHEDULE.get(streak_day, (0.50, 25))
    
    # Credit wallet
    ledger_id = await WalletService.credit(
        account_id=account_id,
        amount=bonus_amount,
        entry_type="daily_bonus",
        description=f"Daily bonus - Day {streak_day}",
        idempotency_key=f"daily_bonus_{account_id}_{today.isoformat()}"
    )
    
    # Add XP
    await GamificationService.add_xp(account_id, xp_amount)
    
    # Update streak
    await GamificationService.update_streak(account_id, current_streak)
    
    # Record claim
    await daily_bonus_claims.insert_one({
        "account_id": account_id,
        "claim_date": today.isoformat(),
        "streak_day": streak_day,
        "bonus_amount": bonus_amount,
        "xp_amount": xp_amount,
        "ledger_entry_id": ledger_id,
        "created_at": datetime.utcnow()
    })
    
    next_claim_at = datetime.combine(today + timedelta(days=1), datetime.min.time())
    
    return DailyBonusResponse(
        claimed=True,
        streak_day=streak_day,
        bonus_amount=bonus_amount,
        xp_amount=xp_amount,
        next_claim_at=next_claim_at
    )
