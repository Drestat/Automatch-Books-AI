from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()

class SetTierRequest(BaseModel):
    target_user_id: str
    tier: str
    token_balance: int = None

@router.post("/set-tier")
async def set_user_tier(
    payload: SetTierRequest,
    x_user_id: str = Header(..., alias="X-User-Id"),
    db: Session = Depends(get_db)
):
    """
    God Mode: Force set a user's tier and optionally token balance.
    Only allows users in settings.ADMIN_USERS to execute this.
    """
    # 1. Verify Admin Access
    if x_user_id not in settings.ADMIN_USERS:
        raise HTTPException(status_code=403, detail="Not authorized for God Mode.")

    # 2. Get Target User
    user = db.query(User).filter(User.id == payload.target_user_id).first()
    if not user:
        # If target is "me", use the requester
        if payload.target_user_id == "me":
            user = db.query(User).filter(User.id == x_user_id).first()
        
        if not user:
             raise HTTPException(status_code=404, detail="Target user not found.")

    # 3. Update Tier
    valid_tiers = ["free", "personal", "business", "corporate", "starter", "pro", "founder", "empire"]
    if payload.tier not in valid_tiers and payload.tier != "expired":
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of {valid_tiers}")

    print(f"⚡ [God Mode] Admin {x_user_id} changing user {user.id} to {payload.tier}")
    
    user.subscription_tier = payload.tier
    user.subscription_status = "active" # Force activate
    
    # 4. Update Token Balance (Optional)
    if payload.token_balance is not None:
        user.token_balance = payload.token_balance
        # Also update allowance to match so it doesn't reset immediately? 
        # Actually user might want to test "running out", so just setting balance is enough.

    db.commit()
    return {
        "status": "success",
        "user_id": user.id,
        "new_tier": user.subscription_tier,
        "new_balance": user.token_balance
    }
