from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.qbo import Base, Transaction, TransactionSplit
from app.services.transaction_service import TransactionService
from unittest.mock import MagicMock, AsyncMock
import asyncio

# Setup in-memory SQLite for testing
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

async def test_split_approval():
    db = SessionLocal()
    # Mock connection
    conn = MagicMock()
    conn.realm_id = "123"
    
    # Create a transaction
    tx = Transaction(
        id="tx_1",
        realm_id="123",
        amount=100.0,
        description="Split Test",
        status="unmatched",
        is_split=True,
        sync_token="0",
        raw_json={"PaymentType": "Expense"}
    )
    db.add(tx)
    
    # Add splits
    s1 = TransactionSplit(transaction_id="tx_1", amount=60.0, category_id="cat_1", category_name="Travel")
    s2 = TransactionSplit(transaction_id="tx_1", amount=40.0, category_id="cat_2", category_name="Meals")
    db.add(s1)
    db.add(s2)
    db.commit()
    
    service = TransactionService(db, conn)
    service.client = MagicMock()
    service.client.request = AsyncMock(return_value={"Purchase": {"SyncToken": "1"}})
    service._resolve_entity_ref = AsyncMock(return_value={"value": "ven_1", "name": "Test Vendor"})
    
    result = await service.approve_transaction("tx_1")
    
    assert result["status"] == "success"
    assert tx.status == "approved"
    assert tx.is_qbo_matched is True
    
    # Verify client call
    call_args = service.client.request.call_args[1]
    payload = call_args["json_payload"]
    assert len(payload["Line"]) == 2
    assert payload["Line"][0]["Amount"] == 60.0
    assert payload["Line"][1]["Amount"] == 40.0
    
    print("✅ Split Approval Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_split_approval())
