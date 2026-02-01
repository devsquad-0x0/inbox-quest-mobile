from fastapi import FastAPI, APIRouter, Request, Response, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import io
from PIL import Image

# Import all routers and services
from app.routers import auth, emails, campaigns, tasks, wallet, gamification, achievements, referrals, tracking
from app.database import db, init_db
from app.middleware.auth_middleware import get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="InboxQuest API", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["Achievements"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referrals"])

# Tracking endpoints (no /api prefix)
app.include_router(tracking.router, tags=["Tracking"])

# Include API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db():
    """Initialize database on startup"""
    await init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    from app.database import client
    client.close()
    logger.info("Database connection closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
