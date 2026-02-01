from fastapi import APIRouter, Depends
from app.models.schemas import ReferralSummary, Referral
from app.middleware.auth_middleware import get_current_user
from app.database import accounts, account_details, referral_rewards
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=ReferralSummary)
async def get_referrals(current_user=Depends(get_current_user)):
    """Get referral program summary"""
    account_id = str(current_user["_id"])
    
    referral_code = current_user.get("referral_code", "")
    referral_link = f"https://t.me/InboxQuestBot?start={referral_code}"
    
    # Get all referred accounts
    referred_accounts = await accounts.find({"referral_account_id": account_id}).to_list(1000)
    
    total_referrals = len(referred_accounts)
    active_referrals = sum(1 for acc in referred_accounts if acc.get("status") == "active")
    
    # Get total earnings from referrals
    referral_rewards_list = await referral_rewards.find({
        "referrer_account_id": account_id,
        "credited_at": {"$ne": None}
    }).to_list(1000)
    
    total_earnings = sum(float(reward.get("reward_amount", 0)) for reward in referral_rewards_list)
    
    # Build referral list with milestones
    referrals = []
    for referred_account in referred_accounts:
        referred_id = str(referred_account["_id"])
        
        # Get account details
        details = await account_details.find_one({"account_id": referred_id})
        
        # Get milestones for this referral
        milestones = await referral_rewards.find({
            "referrer_account_id": account_id,
            "referred_account_id": referred_id,
            "credited_at": {"$ne": None}
        }).to_list(100)
        
        milestones_completed = [m.get("milestone_type", "") for m in milestones]
        total_rewards = sum(float(m.get("reward_amount", 0)) for m in milestones)
        
        referrals.append(Referral(
            referred_account_id=referred_id,
            referred_username=referred_account.get("username", "User"),
            signup_at=referred_account.get("created_at"),
            milestones_completed=milestones_completed,
            total_rewards_earned=total_rewards
        ))
    
    return ReferralSummary(
        referral_code=referral_code,
        referral_link=referral_link,
        total_referrals=total_referrals,
        active_referrals=active_referrals,
        total_earnings=round(total_earnings, 2),
        referrals=referrals
    )
