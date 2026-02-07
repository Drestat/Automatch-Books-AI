import os
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.qbo import Transaction, TransactionSplit, QBOConnection
from app.services.transaction_service import TransactionService

async def verify_splits_receipts():
    db = SessionLocal()
    realm_id = "9341456245321396"

    # Setup: Create Transaction with Splits and Receipt URL
    tx_id = "test-split-receipt-tx"
    tx = Transaction(
        id=tx_id,
        realm_id=realm_id,
        date=datetime.now(),
        description="Split with Receipt",
        amount=100.00,
        currency="USD",
        status="pending_approval", # Set to pending so it runs
        is_split=True,
        receipt_url="/tmp/test_receipt.jpg"
    )
    
    # Create dummy receipt file
    with open("/tmp/test_receipt.jpg", "wb") as f:
        f.write(b"fake_image_data")
        
    # Create Splits
    split1 = TransactionSplit(
        transaction_id=tx_id,
        category_name="Office Supplies",
        category_id="1",
        amount=50.00,
        description="paper"
    )
    split2 = TransactionSplit(
        transaction_id=tx_id,
        category_name="Meals",
        category_id="2",
        amount=50.00,
        description="lunch"
    )
    tx.splits = [split1, split2]
    
    db.merge(tx)
    db.commit()
    print("✅ Created Test Transaction with Splits and Receipt URL")

    # Mock QBO Connection
    conn = QBOConnection(realm_id=realm_id, refresh_token="fresh", access_token="access")
    
    # Initialize Service
    service = TransactionService(db, conn)
    
    # Mock Client
    service.client = MagicMock()
    service.client.request = AsyncMock(return_value={"Purchase": {"Id": tx_id, "SyncToken": "2"}})
    service.client.upload_attachment = AsyncMock(return_value={"Id": "att_1"})
    service._resolve_entity_ref = AsyncMock(return_value={"value": "v1", "name": "Vendor"})
    
    # Run Approve
    print("🚀 Running Approve Transaction (Simulated)...")
    try:
        await service.approve_transaction(tx_id)
        
        # Verify Calls
        # Check Split Update
        service.client.request.assert_awaited()
        call_args = service.client.request.await_args
        if call_args:
            args, kwargs = call_args
            payload = kwargs.get("json_payload", {})
            if len(payload.get("Line", [])) == 2:
                print("✅ Split Update Payload Verified (2 Lines)")
            else:
                 print(f"❌ Split Payload Error. Lines: {len(payload.get('Line', []))}")
        
        # Check Receipt Upload
        service.client.upload_attachment.assert_awaited()
        # Verify mocked file bytes
        ul_args = service.client.upload_attachment.await_args
        if ul_args:
             kwargs = ul_args[1]
             if kwargs.get("filename").startswith("Receipt-") and kwargs.get("file_bytes") == b"fake_image_data":
                 print("✅ Receipt Upload Verified (Correct Filename & Content)")
             else:
                 print(f"❌ Receipt Upload Error. Args: {kwargs}")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    db.query(Transaction).filter(Transaction.id == tx_id).delete()
    db.commit()
    if os.path.exists("/tmp/test_receipt.jpg"):
        os.remove("/tmp/test_receipt.jpg")

if __name__ == "__main__":
    asyncio.run(verify_splits_receipts())
