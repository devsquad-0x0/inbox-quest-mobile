from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Enums
class EmailStatus(str, Enum):
    PENDING = "pending"
    VERIFICATION_SENT = "verification_sent"
    VERIFIED = "verified"
    INVALID = "invalid"
    DISABLED = "disabled"

class TaskStatus(str, Enum):
    PENDING = "pending"
    OPENED = "opened"
    CLICKED = "clicked"
    COMPLETED = "completed"
    REWARDED = "rewarded"
    EXPIRED = "expired"
    FAILED = "failed"

class PayoutStatus(str, Enum):
    REQUESTED = "requested"
    PENDING_REVIEW = "pending_review"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Request/Response Models
class TelegramAuthRequest(BaseModel):
    init_data: str

class UserSession(BaseModel):
    id: str
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    email_verification_status: str = "none"
    referral_code: str
    referred_by: Optional[str] = None
    created_at: datetime

class AuthResponse(BaseModel):
    access_token: str
    expires_at: datetime
    user: UserSession

class EmailResponse(BaseModel):
    id: str
    email: str
    status: str
    verified_at: Optional[datetime] = None

class AddEmailRequest(BaseModel):
    email: EmailStr

class SendVerificationResponse(BaseModel):
    sent: bool
    expires_at: datetime

class VerifyEmailRequest(BaseModel):
    code: str

class VerifyEmailResponse(BaseModel):
    verified: bool

class Campaign(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    vertical_name: Optional[str] = None
    is_subscribed: bool
    active_task_count: int
    status: str

class CampaignListResponse(BaseModel):
    campaigns: List[Campaign]

class SubscribeResponse(BaseModel):
    subscribed: bool

class TaskAssignment(BaseModel):
    id: str
    task_code: str
    campaign_name: str
    campaign_code: str
    action_type: str
    action_number: int
    reward: float
    xp_reward: int
    status: str
    status_label: str
    instructions: str
    email_subject: Optional[str] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class TaskListResponse(BaseModel):
    tasks: List[TaskAssignment]
    total: int
    limit: int
    offset: int

class Wallet(BaseModel):
    available_balance: float
    pending_payouts: float
    total_earnings: float
    currency: str = "USD"
    can_request_payout: bool
    minimum_payout: float
    next_payout_available_at: Optional[datetime] = None

class LedgerEntry(BaseModel):
    id: str
    entry_type: str
    amount: float
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime

class LedgerResponse(BaseModel):
    entries: List[LedgerEntry]
    total: int

class PayoutRequest(BaseModel):
    amount: float
    payout_method: str
    payout_address: str

class PayoutRequestResponse(BaseModel):
    id: str
    amount: float
    currency: str
    payout_method: str
    payout_address: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

class PayoutListResponse(BaseModel):
    payouts: List[PayoutRequestResponse]

class UserGamification(BaseModel):
    xp: int
    level: int
    level_name: str
    xp_to_next_level: int
    xp_progress: int  # 0-100 percentage
    current_streak: int
    longest_streak: int
    tasks_completed: int
    daily_bonus_available: bool
    daily_bonus_streak_day: int  # 1-7

class DailyBonusResponse(BaseModel):
    claimed: bool
    streak_day: int
    bonus_amount: float
    xp_amount: int
    next_claim_at: datetime

class Achievement(BaseModel):
    id: str
    code: str
    name: str
    description: str
    category: str
    icon: str
    requirement_value: int
    xp_reward: int
    cash_reward: float
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    progress: int
    progress_percent: int  # 0-100

class AchievementListResponse(BaseModel):
    achievements: List[Achievement]

class Referral(BaseModel):
    referred_account_id: str
    referred_username: str
    signup_at: datetime
    milestones_completed: List[str]
    total_rewards_earned: float

class ReferralSummary(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    active_referrals: int
    total_earnings: float
    referrals: List[Referral]
