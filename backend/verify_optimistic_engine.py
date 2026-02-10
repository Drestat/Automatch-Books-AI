import os
import sys
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.qbo import Transaction, QBOConnection, BankAccount
from app.services.transaction_service import TransactionService

async def verify_optimistic():
    print("🧪 [Verify] Starting Optimistic Engine Verification...")
    
    # Mock Transaction
    tx = Transaction(
        id="tx_123", 
        realm_id="test_realm", 
        status="pending_approval", 
        category_id="cat_1",
        category_name="Travel",
        tags=[],
        raw_json={}
    )

    # Mock DB and Connection
    db = MagicMock()
    conn = QBOConnection(realm_id="test_realm", user_id="test_user")
    
    # Mock DB behavior
    def mock_query(model):
        query = MagicMock()
        filter_mock = MagicMock()
        query.filter.return_value = filter_mock
        if model.__name__ == "Transaction":
            filter_mock.first.return_value = tx
        elif model.__name__ == "BankAccount":
            filter_mock.first.return_value = BankAccount(name="Checking")
        return query

    db.query.side_effect = mock_query
    
    service = TransactionService(db, conn)
    service.client = MagicMock()
    service.client.update_purchase = AsyncMock(return_value={"SyncToken": "2"})
    service._upload_receipt = AsyncMock()
    service._resolve_entity_ref = AsyncMock(return_value={"value": "v1", "name": "Vendor"})

    # 1. Test Optimistic Approval
    print("\n🚀 Testing Optimistic Approval...")
    res = await service.approve_transaction("tx_123", optimistic=True)
    
    assert tx.status == "pending_qbo"
    assert res["status"] == "success"
    print("✅ Local status moved to 'pending_qbo' immediately.")

    # 2. Test Background Sync
    print("\n🔗 Testing Background Sync Worker logic...")
    sync_res = await service.sync_approved_to_qbo("tx_123")
    
    assert tx.status == "approved"
    assert tx.is_qbo_matched is True
    assert sync_res["status"] == "success"
    service.client.update_purchase.assert_called_once()
    print("✅ Background sync completed. Status moved to 'approved'.")

    # 3. Test Error Case
    print("\n❌ Testing Sync Error Handling...")
    tx.status = "pending_qbo"
    service.client.update_purchase.side_effect = Exception("QBO API Offline")
    
    try:
        await service.sync_approved_to_qbo("tx_123")
    except:
        pass
        
    assert tx.status == "error_qbo"
    assert "QBO API Offline" in tx.reasoning
    print("✅ Error handled. Status moved to 'error_qbo' with reasoning.")

    print("\n🎉 [Verify] Optimistic Engine Logic Verified.")

if __name__ == "__main__":
    asyncio.run(verify_optimistic())
