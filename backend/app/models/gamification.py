from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.session import Base

class UserGamificationStats(Base):
    __tablename__ = "user_gamification_stats"
    
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    total_xp = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    streak_freeze_count = Column(Integer, default=0)
    last_freeze_use_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to User (optional, if you want back-populates)
    # user = relationship("User", back_populates="gamification_stats")

class GamificationEvent(Base):
    __tablename__ = "gamification_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False) # 'categorize', 'rule_create', 'inbox_zero', 'daily_bonus'
    xp_earned = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True) # avoiding reserved word conflict if any
    created_at = Column(DateTime(timezone=True), server_default=func.now())
