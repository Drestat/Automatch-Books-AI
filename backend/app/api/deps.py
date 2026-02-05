from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.session import get_db
from app.models.user import User
from app.models.qbo import QBOConnection

def get_subscription_status(user: User):
    """
    Computes subscription status.
    Returns: active, trial, expired, no_plan
    """
    if user.subscription_tier in ['pro', 'founder', 'empire']:
        return "active"
    
    if user.subscription_tier == 'free':
        if user.trial_ends_at:
            now = datetime.now(timezone.utc)
            if user.trial_ends_at > now:
                return "trial"
            else:
                return "expired"
        else:
            return "no_plan"
            
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
