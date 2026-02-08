import asyncio
import os
from app.db.session import SessionLocal
from app.models.qbo import Transaction, QBOConnection
from app.services.qbo_client import QBOClient
from app.core.config import settings

async def debug_update():
    db = SessionLocal()
    try:
        # Get a recent SalesReceipt or RefundReceipt
        tx = db.query(Transaction).filter(
            Transaction.transaction_type.in_(["SalesReceipt", "RefundReceipt", "CreditMemo"]),
            Transaction.sync_token.isnot(None)
        ).order_by(Transaction.date.desc()).first()
        
        if not tx:
            print("❌ No Sales/Refund entries found to test.")
            return

        print(f"🔍 Testing update for {tx.transaction_type} {tx.id} (SyncToken: {tx.sync_token})")
        
        conn = db.query(QBOConnection).filter(QBOConnection.realm_id == tx.realm_id).first()
        if not conn:
            print("❌ No QBO connection found.")
            return
            
        client = QBOClient(db, conn)
        
        # Scenario 1: Update with category (ItemAccountRef)
        print("\n--- Scenario 1: Update with Category (via ItemAccountRef) ---")
        try:
            # Re-fetch from QBO for latest sync token
            query_res = await client.query(f"SELECT * FROM {tx.transaction_type} WHERE Id = '{tx.id}'")
            latest_token = query_res.get("QueryResponse", {}).get(tx.transaction_type, [{}])[0].get("SyncToken")
            
            print(f"Found latest SyncToken: {latest_token}")
            
            # Using the same category it already has, just to test the update path
            res = await client.update_purchase(
                purchase_id=tx.id,
                category_id=tx.suggested_category_id or tx.category_id,
                category_name="Testing",
                sync_token=latest_token,
                entity_type=tx.transaction_type,
            )
            print("✅ Scenario 1 Success!")
        except Exception as e:
            print(f"❌ Scenario 1 Failed: {e}")

        # Scenario 2: Update without line (Pure sparse header)
        print("\n--- Scenario 2: Update without Line (Pure sparse header) ---")
        try:
            query_res = await client.query(f"SELECT * FROM {tx.transaction_type} WHERE Id = '{tx.id}'")
            latest_token = query_res.get("QueryResponse", {}).get(tx.transaction_type, [{}])[0].get("SyncToken")
            
            res = await client.update_purchase(
                purchase_id=tx.id,
                category_id=None,
                category_name=None,
                sync_token=latest_token,
                entity_type=tx.transaction_type,
                append_memo="#DebugMatch",
            )
            print("✅ Scenario 2 Success!")
        except Exception as e:
            print(f"❌ Scenario 2 Failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_update())
