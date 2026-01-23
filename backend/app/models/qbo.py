from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, UUID
from sqlalchemy.sql import func
from app.db.session import Base
import uuid


class QBOConnection(Base):
    __tablename__ = "qbo_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    realm_id = Column(String, unique=True, index=True, nullable=False)
    refresh_token = Column(String, nullable=False)
    access_token = Column(String)
    expires_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

from sqlalchemy.orm import relationship

class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True)
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    name = Column(String)
    type = Column(String)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True)
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    display_name = Column(String)
    fully_qualified_name = Column(String)
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
    
    # AI Suggestions (Main / Single)
    suggested_category_id = Column(String)
    suggested_category_name = Column(String)
    reasoning = Column(String)
    confidence = Column(Numeric(3, 2))
    
    # Splitting support
    is_split = Column(JSON, default=False) # Store True or details
    splits = relationship("TransactionSplit", back_populates="transaction", cascade="all, delete-orphan")
    
    raw_json = Column(JSON)
    
    # Receipt Mirroring
    receipt_url = Column(String, nullable=True)
    receipt_data = Column(JSON, nullable=True) # AI extracted info
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransactionSplit(Base):
    __tablename__ = "transaction_splits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String, ForeignKey("transactions.id", ondelete="CASCADE"))
    category_id = Column(String)
    category_name = Column(String)
    amount = Column(Numeric(15, 2))
    description = Column(String)
    
    transaction = relationship("Transaction", back_populates="splits")
