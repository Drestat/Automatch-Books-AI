from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, UUID
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QBOConnection(Base):
    __tablename__ = "qbo_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    realm_id = Column(String, unique=True, index=True, nullable=False)
    refresh_token = Column(String, nullable=False)
    access_token = Column(String)
    expires_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True) # QBO Id
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    date = Column(DateTime(timezone=True))
    description = Column(String)
    amount = Column(Numeric(15, 2))
    currency = Column(String)
    account_id = Column(String)
    account_name = Column(String)
    status = Column(String, default="unmatched") # unmatched, pending_approval, approved
    suggested_category_id = Column(String)
    suggested_category_name = Column(String)
    reasoning = Column(String)
    confidence = Column(Numeric(3, 2))
    raw_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
