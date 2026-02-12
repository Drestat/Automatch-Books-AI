from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.user import User
from app.models.qbo import QBOConnection
from typing import Optional

def get_current_user(x_user_id: str = Header(..., alias="X-User-Id"), db: Session = Depends(get_db)) -> User:
    """
    Retrieves the current user based on the X-User-Id header.
    Auto-creates the user if they don't exist yet (lazy registration from Clerk).
    """
    user = db.query(User).filter(User.id == x_user_id).first()
    if not user:
        # Lazy Registration: Create user if they exist in Clerk but haven't been synced yet
        user = User(
            id=x_user_id,
            email=f"{x_user_id}@clerk.internal",
            subscription_tier="free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_subscription_status(user: User):
    """
    Computes subscription status.
    Returns: active, no_plan
    """
    # All recognized tiers are active
    VALID_TIERS = {'free', 'free_user', 'personal', 'business', 'corporate', 'starter', 'pro', 'founder', 'empire'}
    if user.subscription_tier in VALID_TIERS:
        return "active"
    
    return "no_plan"

async def verify_subscription(realm_id: str, db: Session = Depends(get_db)):
    """
    Dependency to ensure the user has an active subscription or trial.
    """
    connection = db.query(QBOConnection).filter(QBOConnection.realm_id == realm_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="QBO Connection not found")
        
    user = db.query(User).filter(User.id == connection.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    status = get_subscription_status(user)
    
    if status in ['expired', 'no_plan']:
        # HTTP 402 is Payment Required
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "subscription_required",
                "message": "Your trial has expired. Please upgrade to a paid plan to continue.",
                "tier": user.subscription_tier
            }
        )
    
    return user
