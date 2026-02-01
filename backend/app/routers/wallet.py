from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.schemas import Wallet, LedgerResponse, LedgerEntry, PayoutRequest, PayoutRequestResponse, PayoutListResponse
from app.middleware.auth_middleware import get_current_user
from app.database import wallet_ledger, payout_requests, accounts
from app.services.wallet_service import WalletService
from app.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=Wallet)
async def get_wallet(current_user=Depends(get_current_user)):
    """Get wallet summary"""
    account_id = str(current_user["_id"])
    
    available_balance = await WalletService.get_balance(account_id)
    pending_payouts = await WalletService.get_pending_payouts(account_id)
    total_earnings = await WalletService.get_total_earnings(account_id)
    
    # Check payout eligibility
    can_request_payout = True
    next_payout_available_at = None
    
    # Check minimum balance
    if available_balance < settings.MINIMUM_PAYOUT:
        can_request_payout = False
    
    # Check account age
    created_at = current_user.get("created_at")
    if created_at:
        account_age = (datetime.utcnow() - created_at).days
        if account_age < settings.MINIMUM_ACCOUNT_AGE_DAYS:
            can_request_payout = False
            next_payout_available_at = created_at + timedelta(days=settings.MINIMUM_ACCOUNT_AGE_DAYS)
    
    # Check cooldown
    last_payout = await payout_requests.find_one(
        {"account_id": account_id, "status": {"$in": ["paid", "processing"]}},
        sort=[("created_at", -1)]
    )
    if last_payout:
        cooldown_end = last_payout["created_at"] + timedelta(days=settings.PAYOUT_COOLDOWN_DAYS)
        if datetime.utcnow() < cooldown_end:
            can_request_payout = False
            next_payout_available_at = cooldown_end
    
    return Wallet(
        available_balance=round(available_balance, 2),
        pending_payouts=round(pending_payouts, 2),
        total_earnings=round(total_earnings, 2),
        currency="USD",
        can_request_payout=can_request_payout,
        minimum_payout=settings.MINIMUM_PAYOUT,
        next_payout_available_at=next_payout_available_at
    )

@router.get("/ledger", response_model=LedgerResponse)
async def get_ledger(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    entry_type: str = Query(None),
    current_user=Depends(get_current_user)
):
    """Get transaction history"""
    account_id = str(current_user["_id"])
    
    query = {"account_id": account_id}
    if entry_type:
        query["entry_type"] = {"$in": entry_type.split(",")}
    
    total = await wallet_ledger.count_documents(query)
    entries_list = await wallet_ledger.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    entries = [
        LedgerEntry(
            id=str(entry["_id"]),
            entry_type=entry.get("entry_type", ""),
            amount=float(entry.get("amount", 0)),
            description=entry.get("description", ""),
            reference_type=entry.get("reference_type"),
            reference_id=entry.get("reference_id"),
            created_at=entry.get("created_at", datetime.utcnow())
        )
        for entry in entries_list
    ]
    
    return LedgerResponse(entries=entries, total=total)

@router.post("/payouts", response_model=PayoutRequestResponse)
async def request_payout(request: PayoutRequest, current_user=Depends(get_current_user)):
    """Request a payout"""
    account_id = str(current_user["_id"])
    
    # Validate balance
    available_balance = await WalletService.get_balance(account_id)
    if request.amount > available_balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")
    
    if request.amount < settings.MINIMUM_PAYOUT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum payout is ${settings.MINIMUM_PAYOUT}"
        )
    
    # Create payout request
    payout_doc = {
        "account_id": account_id,
        "amount": request.amount,
        "currency": "USD",
        "payout_method": request.payout_method,
        "payout_address": request.payout_address,
        "status": "requested",
        "created_at": datetime.utcnow(),
        "created_by": 1
    }
    
    result = await payout_requests.insert_one(payout_doc)
    
    # Debit wallet
    await WalletService.credit(
        account_id=account_id,
        amount=-request.amount,
        entry_type="payout",
        reference_type="payout_request",
        reference_id=str(result.inserted_id),
        description=f"Payout request - {request.payout_method}"
    )
    
    return PayoutRequestResponse(
        id=str(result.inserted_id),
        amount=request.amount,
        currency="USD",
        payout_method=request.payout_method,
        payout_address=request.payout_address,
        status="requested",
        created_at=datetime.utcnow()
    )

@router.get("/payouts", response_model=PayoutListResponse)
async def get_payouts(current_user=Depends(get_current_user)):
    """Get payout history"""
    account_id = str(current_user["_id"])
    
    payout_list = await payout_requests.find({"account_id": account_id}).sort("created_at", -1).to_list(100)
    
    payouts = [
        PayoutRequestResponse(
            id=str(payout["_id"]),
            amount=float(payout.get("amount", 0)),
            currency=payout.get("currency", "USD"),
            payout_method=payout.get("payout_method", ""),
            payout_address=payout.get("payout_address", ""),
            status=payout.get("status", "requested"),
            created_at=payout.get("created_at", datetime.utcnow()),
            processed_at=payout.get("processed_at")
        )
        for payout in payout_list
    ]
    
    return PayoutListResponse(payouts=payouts)
