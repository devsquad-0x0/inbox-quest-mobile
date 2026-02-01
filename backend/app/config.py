import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # App settings
    APP_NAME = "InboxQuest"
    APP_URL = os.getenv("APP_URL", "http://localhost:3000")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
    
    # Database
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = os.environ.get('DB_NAME', 'inboxquest')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8314867460:AAHlAcawVIqUdmD6hMmRbVoKdDHEReYLDs0')
    
    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24 * 7  # 7 days
    
    # Token signing for tracking
    TOKEN_SIGNING_KEY = os.environ.get('TOKEN_SIGNING_KEY', 'tracking-secret-key-change-in-production')
    TOKEN_EXPIRATION_DAYS = 7
    
    # Wallet
    MINIMUM_PAYOUT = 10.0
    PAYOUT_COOLDOWN_DAYS = 7
    MINIMUM_ACCOUNT_AGE_DAYS = 7
    
    # Gamification
    LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 2000, 4000, 8000, 15000, 30000]
    LEVEL_NAMES = [
        "Newcomer", "Beginner", "Apprentice", "Skilled", "Expert",
        "Master", "Elite", "Champion", "Legend", "Grandmaster"
    ]
    
    # Daily bonus schedule (day -> (cash, xp))
    DAILY_BONUS_SCHEDULE = {
        1: (0.50, 25),
        2: (0.75, 25),
        3: (1.00, 25),
        4: (1.50, 25),
        5: (2.00, 25),
        6: (3.00, 25),
        7: (5.00, 50)
    }
    
    # Referral rewards
    REFERRAL_REWARDS = {
        'signup': 0.00,
        'email_verified': 0.25,
        'first_task': 0.50,
        'first_payout': 1.00,
        'tasks_10': 1.00,
        'tasks_50': 2.50
    }
    
    # Email (mock for now)
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'noreply@inboxquest.com')

settings = Settings()
