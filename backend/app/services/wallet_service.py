from datetime import datetime
from typing import Optional
from app.database import wallet_ledger, payout_requests
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class WalletService:
    """Service for wallet operations"""
    
    @staticmethod
    async def get_balance(account_id: str) -> float:
        """Calculate current balance from ledger"""
        pipeline = [
            {"$match": {"account_id": account_id}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await wallet_ledger.aggregate(pipeline).to_list(1)
        return float(result[0]["total"]) if result else 0.0
    
    @staticmethod
    async def get_pending_payouts(account_id: str) -> float:
        """Get total pending payout amounts"""
        pipeline = [
            {"$match": {
                "account_id": account_id,
                "status": {"$in": ["requested", "pending_review", "processing"]}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await payout_requests.aggregate(pipeline).to_list(1)
        return float(result[0]["total"]) if result else 0.0
    
    @staticmethod
    async def get_total_earnings(account_id: str) -> float:
        """Get total earnings (all positive ledger entries)"""
        pipeline = [
            {"$match": {"account_id": account_id, "amount": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await wallet_ledger.aggregate(pipeline).to_list(1)
        return float(result[0]["total"]) if result else 0.0
    
    @staticmethod
    async def credit(
        account_id: str,
        amount: float,
        entry_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: str = "",
        idempotency_key: Optional[str] = None
    ) -> Optional[str]:
        """Credit wallet with idempotency"""
        try:
            entry = {
                "account_id": account_id,
                "entry_type": entry_type,
                "amount": float(amount),
                "currency": "USD",
                "reference_type": reference_type,
                "reference_id": reference_id,
                "description": description,
                "created_at": datetime.utcnow()
            }
            
            if idempotency_key:
                entry["idempotency_key"] = idempotency_key
                
                # Check if already exists
                existing = await wallet_ledger.find_one({"idempotency_key": idempotency_key})
                if existing:
                    logger.info(f"Idempotent credit already exists: {idempotency_key}")
                    return str(existing["_id"])
            
            result = await wallet_ledger.insert_one(entry)
            logger.info(f"Credited {amount} to account {account_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error crediting wallet: {str(e)}")
            return None
