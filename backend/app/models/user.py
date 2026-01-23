from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True) # Clerk ID
    email = Column(String, unique=True, index=True, nullable=False)
    subscription_tier = Column(String, default="free")
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive")
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
