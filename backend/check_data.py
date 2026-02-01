import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_data():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'inboxquest')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("📊 Database Status Check:")
    print("=" * 50)
    
    users_count = await db.accounts.count_documents({})
    campaigns_count = await db.campaigns.count_documents({})
    tasks_count = await db.tasks.count_documents({})
    achievements_count = await db.achievements.count_documents({})
    
    print(f"👥 Users: {users_count}")
    print(f"📧 Campaigns: {campaigns_count}")
    print(f"✅ Tasks: {tasks_count}")
    print(f"🏆 Achievements: {achievements_count}")
    print("=" * 50)
    
    if users_count == 0:
        print("✅ Database is clean - No users exist")
    
    if campaigns_count > 0:
        print("✅ Seed data loaded successfully")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
