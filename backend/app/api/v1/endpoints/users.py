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
