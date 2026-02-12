from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserSync, UserPreferences

router = APIRouter()

@router.post("/sync")
def sync_user(user_in: UserSync, db: Session = Depends(get_db)):
    """
    Sync user from Clerk webhook.
    Creates user if not exists, updates if exists.
    """
    user = db.query(User).filter(User.id == user_in.id).first()
    if not user:
        user = User(
            id=user_in.id, 
            email=user_in.email,
            stripe_customer_id=user_in.stripe_customer_id
        )
        db.add(user)
    else:
        user.email = user_in.email
        if user_in.stripe_customer_id:
            user.stripe_customer_id = user_in.stripe_customer_id
    
    db.commit()
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
    Active -> Paid plan
    Trial -> Free plan within 7 days
    Expired -> Free plan after 7 days
    No Plan -> New user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Lazy Registration: Create the user in Postgres if they exist in Clerk
        # but haven't been synced yet (e.g. if webhooks are down)
        user = User(
            id=user_id,
            email=f"{user_id}@clerk.internal", # Unique placeholder, will be updated on next sync
            subscription_tier="free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Calculate computed status
    current_time = func.now()
    
    status = "no_plan"
    days_remaining = 0
    
    if user.subscription_tier in ['personal', 'business', 'corporate', 'starter', 'pro', 'founder', 'empire']:
        status = "active"
    elif user.subscription_tier == 'free':
        status = "active"  # Free forever tier
    else:
        status = "no_plan"

    # Attach computed fields to response (pydantic schema usually filters this, 
    # so we might need to return a dict or update the schema.
    # We'll return a dict to be safe and flexible.)
    return {
        "id": user.id,
        "email": user.email,
        "subscription_status": status,
        "subscription_tier": user.subscription_tier,
        "trial_ends_at": user.trial_ends_at,
        "days_remaining": days_remaining,
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
    
    # Gating check: Auto-accept is only for Founder/Empire
    # However, we allow the DB write if they are premium, but the UI should handle the graying out.
    # On the backend, we should also enforce tier-based execution.
    
    user.auto_accept_enabled = prefs.auto_accept_enabled
    db.commit()
    return {"status": "success", "auto_accept_enabled": user.auto_accept_enabled}
