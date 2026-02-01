from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client
client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

# Collections
accounts = db.accounts
account_details = db.account_details
account_gamification = db.account_gamification
emails = db.emails
confirmation_emails = db.confirmation_emails
isps = db.isps
campaigns = db.campaigns
email_campaigns = db.email_campaigns
offers = db.offers
actions = db.actions
tasks = db.tasks
email_tasks = db.email_tasks
tracking_events = db.tracking_events
wallet_ledger = db.wallet_ledger
payout_requests = db.payout_requests
achievements = db.achievements
account_achievements = db.account_achievements
referral_rewards = db.referral_rewards
daily_bonus_claims = db.daily_bonus_claims

async def init_db():
    """Initialize database with indexes and seed data"""
    logger.info("Initializing database...")
    
    # Create indexes
    await accounts.create_index("username", unique=True)
    await accounts.create_index("referral_code", unique=True)
    await accounts.create_index("status")
    
    await account_details.create_index([("source_type", 1), ("source_id", 1)], unique=True)
    await account_details.create_index("account_id")
    
    await emails.create_index("email", unique=True)
    await emails.create_index("account_id")
    await emails.create_index("is_primary")
    
    await email_tasks.create_index("email_id")
    await email_tasks.create_index("status")
    await email_tasks.create_index("expires_at")
    
    await tracking_events.create_index("email_task_id")
    await tracking_events.create_index([("email_task_id", 1), ("event_type", 1), ("token_nonce", 1)], unique=True)
    
    await wallet_ledger.create_index("account_id")
    await wallet_ledger.create_index("idempotency_key", unique=True, sparse=True)
    
    await payout_requests.create_index("account_id")
    await payout_requests.create_index("status")
    
    await account_gamification.create_index("account_id", unique=True)
    
    await achievements.create_index("code", unique=True)
    
    await account_achievements.create_index([("account_id", 1), ("achievement_id", 1)], unique=True)
    
    await referral_rewards.create_index([("referrer_account_id", 1), ("referred_account_id", 1), ("milestone_type", 1)], unique=True)
    
    await daily_bonus_claims.create_index([("account_id", 1), ("claim_date", 1)], unique=True)
    
    # Seed default data
    await seed_default_data()
    
    logger.info("Database initialization complete")

async def seed_default_data():
    """Seed default data (actions, achievements, ISPs, campaigns)"""
    
    # Seed actions
    default_actions = [
        {"name": "Open Email", "slug": "open", "status": "active"},
        {"name": "Click Link", "slug": "click", "status": "active"}
    ]
    for action in default_actions:
        await actions.update_one(
            {"slug": action["slug"]},
            {"$setOnInsert": action},
            upsert=True
        )
    
    # Seed achievements
    default_achievements = [
        {"code": "first_task", "name": "First Steps", "description": "Complete your first task", "category": "tasks", "requirement_type": "tasks_completed", "requirement_value": 1, "xp_reward": 10, "cash_reward": 0.00, "icon": "trophy", "status": "active"},
        {"code": "tasks_10", "name": "Getting Started", "description": "Complete 10 tasks", "category": "tasks", "requirement_type": "tasks_completed", "requirement_value": 10, "xp_reward": 50, "cash_reward": 0.00, "icon": "star", "status": "active"},
        {"code": "tasks_100", "name": "Task Master", "description": "Complete 100 tasks", "category": "tasks", "requirement_type": "tasks_completed", "requirement_value": 100, "xp_reward": 500, "cash_reward": 1.00, "icon": "medal", "status": "active"},
        {"code": "tasks_500", "name": "Task Legend", "description": "Complete 500 tasks", "category": "tasks", "requirement_type": "tasks_completed", "requirement_value": 500, "xp_reward": 2000, "cash_reward": 5.00, "icon": "crown", "status": "active"},
        {"code": "earnings_1", "name": "First Dollar", "description": "Earn your first dollar", "category": "earnings", "requirement_type": "earnings_total", "requirement_value": 1, "xp_reward": 25, "cash_reward": 0.00, "icon": "dollar", "status": "active"},
        {"code": "earnings_100", "name": "Money Maker", "description": "Earn $100 total", "category": "earnings", "requirement_type": "earnings_total", "requirement_value": 100, "xp_reward": 1000, "cash_reward": 2.00, "icon": "money-bag", "status": "active"},
        {"code": "earnings_500", "name": "High Roller", "description": "Earn $500 total", "category": "earnings", "requirement_type": "earnings_total", "requirement_value": 500, "xp_reward": 3000, "cash_reward": 5.00, "icon": "diamond", "status": "active"},
        {"code": "streak_7", "name": "Consistent", "description": "Maintain a 7-day streak", "category": "streak", "requirement_type": "streak_days", "requirement_value": 7, "xp_reward": 100, "cash_reward": 0.50, "icon": "fire", "status": "active"},
        {"code": "streak_30", "name": "Dedicated", "description": "Maintain a 30-day streak", "category": "streak", "requirement_type": "streak_days", "requirement_value": 30, "xp_reward": 500, "cash_reward": 2.00, "icon": "flame", "status": "active"},
        {"code": "referrals_5", "name": "Social Butterfly", "description": "Refer 5 friends", "category": "referral", "requirement_type": "referrals_count", "requirement_value": 5, "xp_reward": 250, "cash_reward": 1.00, "icon": "users", "status": "active"},
        {"code": "referrals_20", "name": "Influencer", "description": "Refer 20 friends", "category": "referral", "requirement_type": "referrals_count", "requirement_value": 20, "xp_reward": 1000, "cash_reward": 5.00, "icon": "megaphone", "status": "active"},
        {"code": "level_5", "name": "Level Up", "description": "Reach Level 5", "category": "level", "requirement_type": "level_reached", "requirement_value": 5, "xp_reward": 200, "cash_reward": 0.00, "icon": "arrow-up", "status": "active"},
        {"code": "level_10", "name": "Grandmaster", "description": "Reach Level 10", "category": "level", "requirement_type": "level_reached", "requirement_value": 10, "xp_reward": 1000, "cash_reward": 5.00, "icon": "gem", "status": "active"},
    ]
    for achievement in default_achievements:
        await achievements.update_one(
            {"code": achievement["code"]},
            {"$setOnInsert": achievement},
            upsert=True
        )
    
    # Seed ISPs
    default_isps = [
        {"name": "Gmail", "domains": ["gmail.com", "googlemail.com"], "status": "active"},
        {"name": "Yahoo", "domains": ["yahoo.com", "ymail.com", "rocketmail.com"], "status": "active"},
        {"name": "Outlook", "domains": ["outlook.com", "hotmail.com", "live.com", "msn.com"], "status": "active"},
        {"name": "iCloud", "domains": ["icloud.com", "me.com", "mac.com"], "status": "active"},
        {"name": "ProtonMail", "domains": ["protonmail.com", "proton.me"], "status": "active"},
    ]
    for isp in default_isps:
        await isps.update_one(
            {"name": isp["name"]},
            {"$setOnInsert": isp},
            upsert=True
        )
    
    # Seed sample campaigns
    sample_campaigns = [
        {
            "code": "tech_weekly",
            "name": "Tech Weekly Newsletter",
            "description": "Stay updated with the latest tech news and trends",
            "status": "active",
            "vertical_name": "Technology"
        },
        {
            "code": "finance_daily",
            "name": "Finance Daily Digest",
            "description": "Daily financial insights and market updates",
            "status": "active",
            "vertical_name": "Finance"
        },
        {
            "code": "health_tips",
            "name": "Health & Wellness Tips",
            "description": "Weekly health and wellness advice",
            "status": "active",
            "vertical_name": "Health"
        }
    ]
    for campaign in sample_campaigns:
        campaign_doc = await campaigns.find_one({"code": campaign["code"]})
        if not campaign_doc:
            result = await campaigns.insert_one(campaign)
            campaign_id = str(result.inserted_id)
            
            # Create offers for each campaign
            offer_doc = await offers.find_one({"campaign_id": campaign_id})
            if not offer_doc:
                offer_result = await offers.insert_one({
                    "campaign_id": campaign_id,
                    "name": f"{campaign['name']} - Standard Offer",
                    "status": "active"
                })
                offer_id = str(offer_result.inserted_id)
                
                # Create tasks for the offer
                open_action = await actions.find_one({"slug": "open"})
                click_action = await actions.find_one({"slug": "click"})
                
                if open_action and click_action:
                    # Open task
                    await tasks.insert_one({
                        "code": f"{campaign['code']}_open_1",
                        "action_id": str(open_action["_id"]),
                        "action_number": 1,
                        "cost": 0.25,  # $0.25 reward
                        "priority": 1,
                        "status": "active",
                        "offer_id": offer_id
                    })
                    
                    # Click task
                    await tasks.insert_one({
                        "code": f"{campaign['code']}_click_1",
                        "action_id": str(click_action["_id"]),
                        "action_number": 1,
                        "cost": 0.50,  # $0.50 reward
                        "priority": 2,
                        "status": "active",
                        "offer_id": offer_id
                    })
    
    logger.info("Seed data created successfully")
