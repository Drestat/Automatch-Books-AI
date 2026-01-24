from sqlalchemy import Column, String, DateTime, JSON, UUID
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    properties = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Context (optional but useful for robustness)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
