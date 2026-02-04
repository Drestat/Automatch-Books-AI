from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, UUID, Boolean
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

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(String, primary_key=True)
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    display_name = Column(String)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(String, primary_key=True) # QBO Account Id
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    name = Column(String) # Official QBO Name
    nickname = Column(String, nullable=True) # User defined nickname
    currency = Column(String, default="USD")
    balance = Column(Numeric(15, 2), default=0)
    is_active = Column(Boolean, default=False)
    is_connected = Column(Boolean, default=True) # Whether it exists in the latest QBO Bank/CC account list
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Tag(Base):
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    name = Column(String, nullable=False)
    qbo_tag_id = Column(String, nullable=True) # If synced from QBO
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    is_qbo_matched = Column(Boolean, default=False)
    is_excluded = Column(Boolean, default=False)
    is_bank_feed_import = Column(Boolean, default=True)  # False if TxnType=54 (manual entry)
    forced_review = Column(Boolean, default=False)
    transaction_type = Column(String) # Expense, Check, CreditCard, etc.
    note = Column(String) # User editable note (initially from Memo)
    payee = Column(String, nullable=True) # Vendor or Customer name
    tags = Column(JSON, default=[]) # List of strings
    suggested_tags = Column(JSON, default=[]) # AI suggested tags
    status = Column(String, default="unmatched") # unmatched, pending_approval, approved
    sync_token = Column(String) # QBO SyncToken for optimistic locking
    
    # AI Suggestions (Main / Single)
    suggested_category_id = Column(String)
    suggested_category_name = Column(String)
    reasoning = Column(String)
    vendor_reasoning = Column(String)
    category_reasoning = Column(String)
    note_reasoning = Column(String)
    tax_deduction_note = Column(String)
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

class SyncLog(Base):
    __tablename__ = "sync_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    realm_id = Column(String, ForeignKey("qbo_connections.realm_id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    entity_type = Column(String) # transactions, categories, customers
    operation = Column(String) # sync, ai_analysis, receipt_match
    count = Column(Numeric, default=0)
    status = Column(String) # success, partial_failure, error
    details = Column(JSON, nullable=True)
