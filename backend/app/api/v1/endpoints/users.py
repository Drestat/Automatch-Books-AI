from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserSync, UserPreferences

router = APIRouter()

# All valid subscription tiers in the system
VALID_TIERS = {'free', 'personal', 'business', 'corporate', 'starter', 'pro', 'founder', 'empire'}

# Token allowances per tier
TIER_TOKEN_ALLOWANCES = {
    'free': 50,
    'personal': 200,
    'business': 500,
    'corporate': 2000,
    'starter': 200,
    'pro': 500,
    'founder': 2000,
    'empire': 5000,
}

@router.post("/sync")
def sync_user(user_in: UserSync, db: Session = Depends(get_db)):
    """
    Sync user from Clerk webhook or Stripe webhook.
    Creates user if not exists, updates if exists.
    Handles: email, stripe_customer_id, subscription_tier, subscription_status.
    """
    user = db.query(User).filter(User.id == user_in.id).first()
    if not user:
        user = User(
            id=user_in.id, 
            email=user_in.email or f"{user_in.id}@clerk.internal",
            stripe_customer_id=user_in.stripe_customer_id,
            subscription_tier=user_in.subscription_tier or "free",
        )
        db.add(user)
    else:
        # Update fields only if provided (non-None)
        if user_in.email:
            user.email = user_in.email
        if user_in.stripe_customer_id:
            user.stripe_customer_id = user_in.stripe_customer_id
        if user_in.subscription_tier and user_in.subscription_tier in VALID_TIERS:
            user.subscription_tier = user_in.subscription_tier
            # Update token allowance when tier changes
            user.monthly_token_allowance = TIER_TOKEN_ALLOWANCES.get(user_in.subscription_tier, 50)
            # Grant tokens immediately on upgrade
            if user.token_balance < user.monthly_token_allowance:
                user.token_balance = user.monthly_token_allowance
        if user_in.subscription_status:
            user.subscription_status = user_in.subscription_status
    
    db.commit()
    return {"status": "synced"}

@router.get("/me")
def fetch_my_profile(user_id: str, db: Session = Depends(get_db)):
    """
    Proxy to get_user for 'me' path, using query param.
    """
    return get_user(user_id, db)

@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get user by ID with computed subscription status.
    Active -> Paid plan or free plan
    No Plan -> Unknown tier
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Lazy Registration: Create the user in Postgres if they exist in Clerk
        # but haven't been synced yet (e.g. if webhooks are down)
        user = User(
            id=user_id,
            email=f"{user_id}@clerk.internal",
            subscription_tier="free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Calculate computed status
    if user.subscription_tier in VALID_TIERS:
        status = "active"
    else:
        status = "no_plan"

    return {
        "id": user.id,
        "email": user.email,
        "subscription_status": status,
        "subscription_tier": user.subscription_tier,
        "trial_ends_at": user.trial_ends_at,
        "days_remaining": 0,
        "token_balance": user.token_balance,
        "monthly_token_allowance": user.monthly_token_allowance,
        "auto_accept_enabled": user.auto_accept_enabled
    }

@router.patch("/{user_id}/preferences")
def update_user_preferences(
    user_id: str, 
    prefs: UserPreferences, 
    db: Session = Depends(get_db)
):
    """
    Update user preferences like Auto-Accept.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.auto_accept_enabled = prefs.auto_accept_enabled
    db.commit()
    return {"status": "success", "auto_accept_enabled": user.auto_accept_enabled}
