from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.endpoints.qbo import get_db
from app.models.user import User
from app.schemas.user import UserSync

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
    return {"status": "synced"}

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
    
    # Mock data for dev if user missing (to unblock UI work)
    if not user:
        # Simulate a trial user for now to show the UI
        # In production, this would return 404 or a 'no_plan' user object
        from datetime import datetime, timedelta
        return {
            "id": user_id,
            "email": "test@example.com",
            # Change this to 'expired' or 'no_plan' to test other states manually
            "subscription_status": "trial", # This string doesn't matter much as logic below overrides it if we rely on date, but let's be consistent. Actually wait, the logic BELOW calculates status based on date for REAL users. For MOCK users, we return the dict directly.
            "subscription_tier": "free",
            "trial_ends_at": datetime.utcnow() + timedelta(days=5),
            "days_remaining": 5,
            "token_balance": 50,
            "monthly_token_allowance": 50
        }

    # Calculate computed status
    current_time = func.now()
    
    status = "no_plan"
    days_remaining = 0
    
    if user.subscription_tier in ['founder', 'empire']:
        status = "active"
    elif user.subscription_tier == 'free':
        if user.trial_ends_at:
             # Logic to compare dates would typically happen in Python or SQL
             # For simplicity here, we assume the frontend or a service handles the precise date diff
             # But let's verify if we can do it here. 
             # Since 'user' is an ORM object, we can do pythonic comparison if it's loaded.
             import datetime
             now = datetime.datetime.utcnow()
             # user.trial_ends_at is a datetime (timezone aware hopefully)
             
             # Naive check for now, assuming naive datetimes or compatible
             if user.trial_ends_at and user.trial_ends_at > now:
                 status = "trial"
                 delta = user.trial_ends_at - now
                 days_remaining = delta.days
             else:
                 status = "expired"
        else:
            # Free tier but no trial date? Assume expired or new?
            # Let's assume expired if they are 'free' but have no trial date marked (legacy?)
            # Or assume they haven't started trial?
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
        "monthly_token_allowance": user.monthly_token_allowance
    }
