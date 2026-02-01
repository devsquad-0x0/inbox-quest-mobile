import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def reset_database():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'inboxquest')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🗑️  Dropping all collections...")
    
    # Get all collection names
    collections = await db.list_collection_names()
    
    for collection_name in collections:
        await db[collection_name].drop()
        print(f"   ✅ Dropped: {collection_name}")
    
    print("\n✅ Database reset complete!")
    print("All users and data have been deleted.")
    print("\nNext steps:")
    print("1. Restart backend to recreate seed data")
    print("2. Test the app fresh")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_database())
