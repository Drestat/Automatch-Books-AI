from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.qbo import User
import uuid

def get_current_user(x_user_id: str = Header(...), db: Session = Depends(get_db)) -> User:
    """
    Simulates auth by trusting X-User-ID header.
    In production, this should verify a Bearer token (Clerk/Auth0).
    """
    try:
        user_uuid = uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
